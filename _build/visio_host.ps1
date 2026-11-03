# Visio drawing host: reads a UTF-8 JSON spec and builds a .vsdx page, then exports PNG/PDF.
# Usage: powershell -NoProfile -File visio_host.ps1 -Spec <path.json>
param(
    [Parameter(Mandatory = $true)][string]$Spec,
    [string]$OutVsdx = '',
    [string]$OutPng = '',
    [string]$OutPdf = '',
    [string]$PageName = 'Page-1'
)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$plan = Get-Content -LiteralPath $Spec -Raw -Encoding UTF8 | ConvertFrom-Json

$PT = 1.0 / 72.0   # 1 point expressed in inches (Visio internal unit)
$INV = [System.Globalization.CultureInfo]::InvariantCulture

# Visio formulas always use '.' as the decimal separator, so numbers are
# formatted invariantly no matter what the host locale is.
function Fmt {
    param($Value)
    return ([double]$Value).ToString('0.######', $INV)
}

# Colours are written as a guarded RGB() formula: Visio parses a bare
# "#ffffff" as the hex number 0 (black), and the guard stops themes from
# overriding the explicit colour.
function FmtColor {
    param($Value)
    $s = ([string]$Value).TrimStart('#')
    if ($s.Length -ne 6) { throw "colour must look like #RRGGBB, got '$Value'" }
    $r = [Convert]::ToInt32($s.Substring(0, 2), 16)
    $g = [Convert]::ToInt32($s.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($s.Substring(4, 2), 16)
    return "THEMEGUARD(RGB($r,$g,$b))"
}

$diag = New-Object System.Collections.Generic.List[string]
function D {
    param($Message)
    $diag.Add([string]$Message)
}

# Visio exposes Characters as a method and Cells as a parameterized property;
# both are probed so the host works across PowerShell / interop combinations.
function Get-Chars {
    param($Shape)
    try { return $Shape.Characters() } catch { return $Shape.Characters }
}

function Get-Cell {
    param($Shape, $Name)
    return $Shape.Cells($Name)
}

function Set-Cell {
    param($Shape, $Name, $Formula)
    $Shape.Cells($Name).FormulaForceU = $Formula
    $st = [int]$Shape.Cells($Name).Stat
    if ($st -ne 0) { throw "cell '$Name' rejected formula '$Formula' (Stat=$st)" }
}

# Visio returns a Cell whose value is '#NAME?' for a cell that does not exist
# instead of throwing, so optional cell writes are guarded by CellExists.
function Set-CellIf {
    param($Shape, $Name, $Formula)
    $ok = $false
    try { $ok = [bool]$Shape.CellExists($Name, 0) } catch { $ok = $false }
    if ($ok) {
        $Shape.Cells($Name).FormulaForceU = $Formula
        $st = [int]$Shape.Cells($Name).Stat
        if ($st -ne 0) { throw "optional cell '$Name' rejected formula '$Formula' (Stat=$st)" }
    }
}

# Shorthand cell writers for the styling cells used by the drawing spec.
function Set-LineWeight { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'LineWeight' -Formula (Fmt $Value) }
function Set-LineColor { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'LineColor' -Formula (FmtColor $Value) }
function Set-LinePattern { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'LinePattern' -Formula (Fmt $Value) }
function Set-FillForegnd { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'FillForegnd' -Formula (FmtColor $Value) }
function Set-FillPattern { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'FillPattern' -Formula (Fmt $Value) }
function Set-EndArrow { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'EndArrow' -Formula (Fmt $Value) }
function Set-BeginArrow { param($Shape, $Value) Set-CellIf -Shape $Shape -Name 'BeginArrow' -Formula (Fmt $Value) }

function Set-Text {
    param($Shape, $Text, $Font, $SizePt, $Style, $Color)
    $Shape.Text = $Text
    try {
        # Visio section indices: 3 = Character, 4 = Paragraph.
        # CellsSRC is used because the Characters interop object exposes no
        # settable Font/Size properties in this host.
        $bits = 0
        if ($Style -eq 'bold') { $bits = $bits + 1 }
        if ($Style -eq 'italic') { $bits = $bits + 2 }
        $Shape.CellsSRC(3, 0, 0).FormulaForceU = '"' + $Font + '"'          # Char.Font
        $Shape.CellsSRC(3, 0, 2).FormulaForceU = (Fmt $bits)                # Char.Style
        foreach ($row in 0..4) {
            $Shape.CellsSRC(3, $row, 7).FormulaForceU = (Fmt ($SizePt * $PT)) + ' in'   # Char.Size
        }
        if ($Color) {
            $Shape.CellsSRC(3, 0, 1).FormulaForceU = (FmtColor $Color)     # Char.Color
        }
    } catch {
        Write-Warning "Set-Text failed for '$Text': $_"
    }
}

# Resolves a connection anchor ({key, at}) or an absolute anchor ({x, y}) to coordinates.
function Resolve-Anchor {
    param($Anchor, $Index)
    if ($null -eq $Anchor) { return $null }
    if ($Anchor.PSObject.Properties.Name -contains 'key') {
        $s = $Index[$Anchor.key]
        if ($null -eq $s) { throw "unknown shape key in link: $($Anchor.key)" }
        $x = [double](Get-Cell -Shape $s -Name 'PinX').ResultIU
        $y = [double](Get-Cell -Shape $s -Name 'PinY').ResultIU
        $w = [double](Get-Cell -Shape $s -Name 'Width').ResultIU
        $h = [double](Get-Cell -Shape $s -Name 'Height').ResultIU
        switch ($Anchor.at) {
            'L' { return @(($x - $w / 2), $y) }
            'R' { return @(($x + $w / 2), $y) }
            'T' { return @($x, ($y + $h / 2)) }
            'B' { return @($x, ($y - $h / 2)) }
            default { return @($x, $y) }
        }
    }
    return @([double]$Anchor.x, [double]$Anchor.y)
}

function New-Stick {
    param($App, $Page, $Cx, $Cy, $S, $Color, $Weight, $Label, $Font, $SizePt)
    # The figure occupies the lower part of the group and the label sits just
    # under the feet, so the group stays centred on $Cy where links attach.
    $r = 0.145 * $S
    $hy = $Cy - 0.03 * $S                       # head centre
    $foot = $Cy - 0.50 * $S
    $hip = $Cy - 0.20 * $S
    $parts = @()
    $head = $Page.DrawOval(($Cx - $r), ($hy + $r), ($Cx + $r), ($hy - $r))
    $parts += $head
    $parts += $Page.DrawLine($Cx, ($hy - $r), $Cx, $hip)
    $parts += $Page.DrawLine(($Cx - 0.26 * $S), ($Cy - 0.14 * $S), ($Cx + 0.26 * $S), ($Cy - 0.14 * $S))
    $parts += $Page.DrawLine($Cx, $hip, ($Cx - 0.23 * $S), $foot)
    $parts += $Page.DrawLine($Cx, $hip, ($Cx + 0.23 * $S), $foot)
    foreach ($p in $parts) {
        Set-LineWeight -Shape $p -Value ($Weight * $PT)
        Set-LineColor -Shape $p -Value $Color
        Set-FillPattern -Shape $p -Value 0
    }
    Set-FillPattern -Shape $head -Value 1
    Set-FillForegnd -Shape $head -Value '#ffffff'
    if ($Label) {
        $lbl = $Page.DrawRectangle(($Cx - 0.5 * $S), ($Cy - 0.57 * $S), ($Cx + 0.5 * $S), ($Cy - 0.83 * $S))
        Set-LinePattern -Shape $lbl -Value 0
        Set-FillPattern -Shape $lbl -Value 0
        Set-Text -Shape $lbl -Text $Label -Font $Font -SizePt $SizePt -Style $null -Color $null
        Set-CellIf -Shape $lbl -Name 'VerticalAlign' -Formula '1'
        try { $lbl.CellsSRC(4, 0, 6).FormulaForceU = (Fmt 1) } catch { }
        $parts += $lbl
    }
    $win = $App.ActiveWindow
    $win.DeselectAll()
    foreach ($p in $parts) { $win.Select($p, 2) }   # 2 = visSelect
    $grp = $win.Selection.Group()
    $win.DeselectAll()
    Set-CellIf -Shape $grp -Name 'DisplayLevel' -Formula '0'
    return $grp
}

$app = New-Object -ComObject Visio.Application
$app.Visible = $false
$app.AlertResponse = 7
$app.ScreenUpdating = $false

$phase = 'startup'
try {
$doc = $app.Documents.Add('')
$phase = 'pages-item'
$page = $doc.Pages.Item(1)

$phase = 'page-name'
$page.Name = $PageName
$phase = 'page-size'


Set-Cell -Shape $page.PageSheet -Name 'PageWidth' -Formula "$(Fmt $plan.pageWidth) in"
Set-Cell -Shape $page.PageSheet -Name 'PageHeight' -Formula "$(Fmt $plan.pageHeight) in"

$phase = 'page-orient'
Set-CellIf -Shape $page.PageSheet -Name 'PrintPageOrientation' -Formula '2'
$phase = 'page-snap'
Set-CellIf -Shape $page.PageSheet -Name 'InhibitSnap' -Formula '1'
# 关掉“随图形自动调整页面大小”，否则页面会被内容撑开或裁到贴边
Set-CellIf -Shape $page.PageSheet -Name 'DrawingResizeType' -Formula '0'
$phase = 'page-setup-done'

$index = @{}

# ---- shapes ---------------------------------------------------------------
$si = 0
foreach ($s in $plan.shapes) {
    $si++
    $phase = "shape[$si] type=$($s.type) text=$($s.text)"
    try {
    $sw = [double]$s.strokePt * $PT
    $shape = $null
    $isLine = $false

    switch ($s.type) {
        'rect' {
            $shape = $page.DrawRectangle(($s.x - $s.w / 2), ($s.y + $s.h / 2), ($s.x + $s.w / 2), ($s.y - $s.h / 2))
            if ($null -ne $s.round) { Set-CellIf -Shape $shape -Name 'Rounding' -Formula "$(Fmt $s.round) in" }
            Set-LineWeight -Shape $shape -Value $sw
            Set-LineColor -Shape $shape -Value $s.stroke
            if ($s.fill) { Set-FillForegnd -Shape $shape -Value $s.fill } else { Set-FillPattern -Shape $shape -Value 0 }
            if ($s.dash) { Set-LinePattern -Shape $shape -Value 2 }
            if ($s.noline) { Set-LinePattern -Shape $shape -Value 0 }
        }
        'ellipse' {
            $shape = $page.DrawOval(($s.x - $s.w / 2), ($s.y + $s.h / 2), ($s.x + $s.w / 2), ($s.y - $s.h / 2))
            Set-LineWeight -Shape $shape -Value $sw
            Set-LineColor -Shape $shape -Value $s.stroke
            if ($s.fill) { Set-FillForegnd -Shape $shape -Value $s.fill } else { Set-FillPattern -Shape $shape -Value 0 }
            if ($s.dash) { Set-LinePattern -Shape $shape -Value 2 }
        }
        'line' {
            $shape = $page.DrawLine($s.x1, $s.y1, $s.x2, $s.y2)
            $isLine = $true
            Set-LineWeight -Shape $shape -Value $sw
            Set-LineColor -Shape $shape -Value $s.stroke
            if ($s.dash) { Set-LinePattern -Shape $shape -Value 2 }
            if ($s.endArrow) { Set-EndArrow -Shape $shape -Value ([int]$s.endArrow) }
            if ($s.beginArrow) { Set-BeginArrow -Shape $shape -Value ([int]$s.beginArrow) }
        }
        'poly' {
            $pts = $s.points
            for ($i = 0; $i -lt ($pts.Count - 2); $i++) {
                $seg = $page.DrawLine($pts[$i][0], $pts[$i][1], $pts[$i + 1][0], $pts[$i + 1][1])
                Set-LineWeight -Shape $seg -Value $sw
                Set-LineColor -Shape $seg -Value $s.stroke
                if ($s.dash) { Set-LinePattern -Shape $seg -Value 2 }
            }
            $shape = $page.DrawLine($pts[$pts.Count - 2][0], $pts[$pts.Count - 2][1], $pts[$pts.Count - 1][0], $pts[$pts.Count - 1][1])
            $isLine = $true
            Set-LineWeight -Shape $shape -Value $sw
            Set-LineColor -Shape $shape -Value $s.stroke
            if ($s.dash) { Set-LinePattern -Shape $shape -Value 2 }
            if ($s.endArrow) { Set-EndArrow -Shape $shape -Value ([int]$s.endArrow) }
        }
        'stick' {
            $sizePt = if ($s.sizePt) { $s.sizePt } else { $plan.sizePt }
            $shape = New-Stick -App $app -Page $page -Cx $s.x -Cy $s.y -S $s.scale -Color $s.stroke `
                -Weight $s.strokePt -Label $s.text -Font $plan.font -SizePt $sizePt
        }
        'text' {
            $shape = $page.DrawRectangle(($s.x - $s.w / 2), ($s.y + $s.h / 2), ($s.x + $s.w / 2), ($s.y - $s.h / 2))
            Set-LinePattern -Shape $shape -Value 0
            # a note may want an opaque background so it stays readable over the
            # dashed lifelines; otherwise it is fully transparent
            if ($s.fill) {
                Set-FillPattern -Shape $shape -Value 1
                Set-FillForegnd -Shape $shape -Value $s.fill
            } else {
                Set-FillPattern -Shape $shape -Value 0
            }
            if ($s.anchor -eq 'topleft') {
                Set-CellIf -Shape $shape -Name 'VerticalAlign' -Formula '0'
                try { $shape.CellsSRC(4, 0, 6).FormulaForceU = (Fmt 0) } catch { }
                Set-CellIf -Shape $shape -Name 'TopMargin' -Formula '0.02 in'
            }
        }
        default { throw "unknown shape type: $($s.type)" }
    }

    if ($s.type -ne 'stick') {

        if ($s.align -eq 'left') { $just = 0 } else { $just = 1 }
        # section 4 = Paragraph, col 6 = Para.HorzAlign; vertical centring is
        # the shape's own VerticalAlign cell in section 1.
        try { $shape.CellsSRC(4, 0, 6).FormulaForceU = (Fmt $just) } catch { }
        Set-CellIf -Shape $shape -Name 'VerticalAlign' -Formula '1'
        Set-CellIf -Shape $shape -Name 'LeftMargin' -Formula '0.03 in'
        Set-CellIf -Shape $shape -Name 'RightMargin' -Formula '0.03 in'

        if ($s.text) {
            $sizePt = if ($s.sizePt) { $s.sizePt } else { $plan.sizePt }
            Set-Text -Shape $shape -Text $s.text -Font $plan.font -SizePt $sizePt -Style $s.style -Color $s.textColor
        }

        if ($isLine) {
            Set-CellIf -Shape $shape -Name 'TextBkgnd' -Formula (FmtColor '#ffffff')   # opaque behind line labels
        }
    }

    if ($s.key) { $index[$s.key] = $shape }
    }
    catch {
        $phase = "shape[$si] type=$($s.type) text=$($s.text) :: $($_.Exception.Message)"
        throw
    }
}


# ---- links (drawn after every shape exists) -------------------------------
$li = 0
foreach ($l in $plan.links) {
    $li++
    $phase = "link[$li] $($l.from.key)/$($l.to.key)"
    $a = Resolve-Anchor -Anchor $l.from -Index $index
    $b = Resolve-Anchor -Anchor $l.to -Index $index
    $points = @()
    $points += , @([double]$a[0], [double]$a[1])
    if ($null -ne $l.route) {
        foreach ($r in $l.route) { $points += , @([double]$r[0], [double]$r[1]) }
    }
    $points += , @([double]$b[0], [double]$b[1])

    $lastSeg = $null
    for ($i = 0; $i -lt ($points.Count - 1); $i++) {
        $seg = $page.DrawLine($points[$i][0], $points[$i][1], $points[$i + 1][0], $points[$i + 1][1])
        Set-LineWeight -Shape $seg -Value ([double]$l.strokePt * $PT)
        Set-LineColor -Shape $seg -Value $l.stroke
        if ($l.dash) { Set-LinePattern -Shape $seg -Value 2 }
        if ($l.beginArrow -and $i -eq 0) { Set-BeginArrow -Shape $seg -Value ([int]$l.beginArrow) }
        $lastSeg = $seg
    }
    if ($l.endArrow) { Set-EndArrow -Shape $lastSeg -Value ([int]$l.endArrow) }
    if ($l.text) {
        $mid = [math]::Floor(($points.Count - 1) / 2)
        $ann = $page.DrawLine($points[$mid][0], $points[$mid][1], $points[$mid + 1][0], $points[$mid + 1][1])
        Set-LineWeight -Shape $ann -Value ([double]$l.strokePt * $PT)
        Set-LineColor -Shape $ann -Value $l.stroke
        if ($l.dash) { Set-LinePattern -Shape $ann -Value 2 }
        Set-CellIf -Shape $ann -Name 'TextBkgnd' -Formula (FmtColor '#ffffff')
        Set-Text -Shape $ann -Text $l.text -Font $plan.font -SizePt $plan.sizePt -Style $null -Color $null
    }
}

$app.ScreenUpdating = $true

$phase = 'save'
if ($OutVsdx) {
    foreach ($p in @($OutVsdx, $OutPng, $OutPdf)) {
        if ($p -and (Test-Path -LiteralPath $p)) { Remove-Item -LiteralPath $p -Force }
    }
    $doc.SaveAs($OutVsdx)
    if ($OutPng) { $null = $page.Export($OutPng) }
    if ($OutPdf) { $null = $page.Export($OutPdf) }
}

$doc.Close()
$app.Quit()
Write-Output "BUILT: $OutVsdx"
}
catch {
    Write-Output "HOST-FAIL at phase: $phase"
    Write-Output ("HOST-FAIL message: " + $_.Exception.Message)
    Write-Output ("HOST-FAIL type: " + $_.Exception.GetType().FullName)
    Write-Output ("HOST-FAIL detail: " + ($_ | Out-String))
    try { $doc.Close() } catch { }
    try { $app.Quit() } catch { }
    $diag | ForEach-Object { Write-Output ("DIAG: " + $_) }
    exit 3
}
$diag | ForEach-Object { Write-Output ("DIAG: " + $_) }
