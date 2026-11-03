# 上传到 GitHub（照着做，约 10 分钟）

> 已经帮你准备好的：
> - 仓库分支已改名为 `main`
> - 已生成 SSH 密钥（无口令）
> - 仓库只有 **4.24 MB**，推送很快
> - 实测 `github.com` 可访问，SSH 22 端口通

---

## 第 1 步：注册 / 登录 GitHub

打开 https://github.com ，没有账号就注册一个（用学校邮箱）。

---

## 第 2 步：新建仓库

点右上角 **+** → **New repository**：

| 字段 | 填什么 |
|---|---|
| Repository name | `zhiyu-campus` |
| Description | 知屿校园——校园信息智能平台 |
| 可见性 | **Private**（私有，答辩前别公开） |
| Add a README | ❌ 不要勾 |
| Add .gitignore | ❌ 不要勾 |
| Choose a license | 不选 |

**为什么不勾 README 和 .gitignore**：本地已经有内容了，勾了会导致推送冲突（`rejected: fetch first`），新手最容易卡在这。

---

## 第 3 步：把公钥加到 GitHub

打开 https://github.com/settings/keys → **New SSH key**

| 字段 | 填什么 |
|---|---|
| Title | `我的笔记本` |
| Key type | Authentication Key |
| Key | 复制下面这一整行 |

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGDJnyysp4TtIhYi9A6yXDPyIlNgKDvqnU2kCqBxhDb/ zhiyu-campus
```

点 **Add SSH key**。

> 如果这一行被换行截断了，去 `C:\Users\saxtul\.ssh\id_ed25519.pub` 用记事本打开复制。

---

## 第 4 步：测试连接

```powershell
ssh -T git@github.com
```

第一次会问 `Are you sure you want to continue connecting?`，输入 `yes` 回车。

成功会显示：

```
Hi 你的用户名! You've successfully authenticated...
```

失败会显示 `Permission denied (publickey)`，说明第 3 步没贴对。

---

## 第 5 步：关联远程仓库并推送

把下面的 `你的用户名` 换成 GitHub 用户名：

```powershell
cd "C:\Users\saxtul\Documents\ds harness区\知屿校园"

git remote add origin git@github.com:你的用户名/zhiyu-campus.git
git push -u origin main
git push origin v0.1.0
```

> 标签要单独推，否则 GitHub 上看不到 v0.1.0。

刷新网页，应该能看到 218 个文件和 3 条提交记录。

---

## 第 6 步：让队友能访问

**方式 A：加协作者（推荐，最简单）**

仓库页 → **Settings** → **Collaborators** → **Add people** → 输入队友的 GitHub 用户名或邮箱。

队友会收到邮件，接受后就能 `git clone`。

**方式 B：他们自己改，你审**

他们 fork 你的仓库 → 改完提 Pull Request → 你在网页上点 Merge。

---

## 队友拿到代码后怎么跑

```powershell
git clone git@github.com:你的用户名/zhiyu-campus.git
cd zhiyu-campus

# 1. 建库（需要本机装了 MySQL 8.0）
mysql -u root -p < schema.sql

# 2. 起后端
cd software\campus
.\mvnw.cmd package
java -jar target\campus-0.0.1-SNAPSHOT.jar
```

打开 http://127.0.0.1:8080 ，用 `admin / admin1234` 登录。

> 注意：`schema.sql` 里写死了库名 `zhiyu_campus` 和端口 3307，
> 队友如果用自己的 MySQL，改 `application.yml` 里的连接串即可。

---

## 之后每天怎么用

```powershell
git pull                          # 队友改过就拉下来
# ...改代码...
git add -A
git commit -m "加了帖子筛选"
git push
```

---

## 队友提意见 → 用 Issue 记

这就是解决你"意见太多、不知道做不做"的正解：

1. 队友在 GitHub 上开 **Issue** 写下意见（一个意见一条）
2. 你看到后决定做不做，不做的直接 Close 并说明理由
3. 决定做的，开分支改，提 **Pull Request**，改完合并
4. **所有讨论都留痕**，不会出现"说过但没记、最后扯皮"

建议再开一个保护规则：仓库 Settings → Branches → 保护 `main`，
要求 PR 才能合并。这样队友不能直接覆盖你的主版本。

---

## 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `Permission denied (publickey)` | 公钥没加对 | 重做第 3 步，确认整行复制 |
| `rejected: fetch first` | 建仓库时勾了 README | `git pull --rebase origin main` 后再 push |
| `ssh: connect to host github.com port 22: timed out` | 网络封 22 端口 | 改用 443：见下方 |
| 推送很慢 | 大文件 | 仓库只有 4 MB，正常不该慢；检查是否误传了 target/ |

**SSH 走 443 端口**（22 被封时）：

在 `C:\Users\saxtul\.ssh\config`（没有就新建）里写：

```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
```

然后重新 `ssh -T git@github.com` 测试。

---

## 如果 GitHub 太慢：Gitee 备选

流程一模一样，只是地址换成 `git@gitee.com:用户名/zhiyu-campus.git`。
Gitee 私有仓库免费，国内速度快，但团队成员上限是 5 人，课程项目够用。
