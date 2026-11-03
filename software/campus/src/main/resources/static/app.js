/* 知屿校园 · 前端（Vue 3 + Element Plus，无需构建，随 jar 一起发布） */
const { createApp, reactive } = Vue;

const API = '/api/v1';
const TOKEN_KEY = 'zy_token';
const USER_KEY = 'zy_user';

const state = reactive({
  token: localStorage.getItem(TOKEN_KEY) || '',
  user: JSON.parse(localStorage.getItem(USER_KEY) || 'null')
});

async function api(path, options) {
  const opt = options || {};
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) headers.Authorization = 'Bearer ' + state.token;
  const res = await fetch(API + path, {
    method: opt.method || 'GET',
    headers,
    body: opt.body ? JSON.stringify(opt.body) : undefined
  });
  let json = null;
  try { json = await res.json(); } catch (e) { json = null; }
  if (!res.ok || (json && json.code !== 0)) {
    const err = new Error((json && json.message) || ('请求失败：HTTP ' + res.status));
    err.status = res.status;
    if (res.status === 401) {
      state.token = '';
      state.user = null;
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
    throw err;
  }
  return json ? json.data : null;
}

function parseHash() {
  const raw = (location.hash || '#/posts').replace(/^#/, '');
  const parts = raw.split('/').filter(Boolean);
  if (parts.length === 0) return { name: 'posts' };
  if (parts[0] === 'rooms' && parts[1]) return { name: 'chat', roomId: Number(parts[1]) };
  if (parts[0] === 'posts' && parts[1]) return { name: 'post', postId: Number(parts[1]) };
  return { name: parts[0] };
}

const app = {
  data() {
    return {
      state,
      route: parseHash(),
      loading: false,
      tab: 'login',
      loginForm: { account: '', password: '', nickname: '' },

      tags: [],
      boards: [],

      rooms: [],
      roomDialog: false,
      roomForm: { name: '', intro: '', tagIds: [] },

      currentRoom: null,
      messages: [],
      msgText: '',
      msgCursor: null,
      timer: null,

      posts: [],
      postDialog: false,
      postForm: { boardId: null, title: '', body: '', tagIds: [] },
      filter: { boardId: null, tagId: null, sort: 'latest' },

      currentPost: null,
      replies: [],
      replyText: '',
      aiResult: null,

      searchQ: '',
      searchResults: [],

      pending: [],
      reviewRemark: {}
    };
  },
  computed: {
    isAdmin() {
      return this.state.user && this.state.user.role === 2;
    },
    loggedIn() {
      return !!this.state.token;
    }
  },
  mounted() {
    window.addEventListener('hashchange', this.syncRoute);
    if (!this.loggedIn) {
      location.hash = '#/login';
    } else {
      this.bootstrap();
    }
    this.syncRoute();
  },
  beforeUnmount() {
    this.stopPolling();
  },
  methods: {
    /* ---------------------------------------------------------- 基础 */
    go(path) {
      location.hash = '#' + path;
    },
    syncRoute() {
      this.route = parseHash();
      if (!this.loggedIn && this.route.name !== 'login') {
        this.route = { name: 'login' };
        return;
      }
      this.stopPolling();
      const name = this.route.name;
      if (name === 'rooms') this.loadRooms();
      if (name === 'chat') this.openRoom(this.route.roomId);
      if (name === 'posts') this.loadPosts();
      if (name === 'post') this.openPost(this.route.postId);
      if (name === 'search') this.doSearch();
      if (name === 'review') this.loadPending();
    },
    async bootstrap() {
      try {
        const [tags, boards] = await Promise.all([
          api('/tags'), api('/boards')
        ]);
        this.tags = tags || [];
        this.boards = boards || [];
      } catch (e) {
        ElementPlus.ElMessage.error(e.message);
      }
    },
    notify(msg, type) {
      ElementPlus.ElMessage({ message: msg, type: type || 'success' });
    },
    fail(e) {
      ElementPlus.ElMessage.error(e.message || '操作失败');
    },

    /* ---------------------------------------------------------- 登录 */
    async doLogin() {
      try {
        const data = await api('/auth/login', {
          method: 'POST',
          body: { account: this.loginForm.account, password: this.loginForm.password }
        });
        this.applyAuth(data);
        this.notify('登录成功');
        this.go('/posts');
      } catch (e) { this.fail(e); }
    },
    async doRegister() {
      try {
        await api('/auth/register', {
          method: 'POST',
          body: {
            account: this.loginForm.account,
            nickname: this.loginForm.nickname,
            password: this.loginForm.password
          }
        });
        this.notify('注册成功，请登录');
        this.tab = 'login';
      } catch (e) { this.fail(e); }
    },
    applyAuth(data) {
      state.token = data.accessToken;
      state.user = { id: data.userId, nickname: data.nickname, role: data.role };
      localStorage.setItem(TOKEN_KEY, state.token);
      localStorage.setItem(USER_KEY, JSON.stringify(state.user));
      this.bootstrap();
    },
    logout() {
      this.stopPolling();
      state.token = '';
      state.user = null;
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      this.go('/login');
    },

    /* -------------------------------------------------------- 聊天室 */
    async loadRooms() {
      try {
        const query = this.filter.tagId ? '?tagId=' + this.filter.tagId : '';
        this.rooms = await api('/rooms' + query);
      } catch (e) { this.fail(e); }
    },
    async createRoom() {
      try {
        await api('/rooms', { method: 'POST', body: this.roomForm });
        this.roomDialog = false;
        this.roomForm = { name: '', intro: '', tagIds: [] };
        this.notify('创建成功');
        this.loadRooms();
      } catch (e) { this.fail(e); }
    },
    async joinRoom(room) {
      try {
        await api('/rooms/' + room.id + '/join', { method: 'POST' });
        this.notify('已加入「' + room.name + '」');
      } catch (e) {
        // 40901 表示已经加入过，直接进房间
        if (e.code !== 40901) { this.fail(e); return; }
      }
      // 关键：必须改 hash 触发路由，否则页面不会切到聊天视图
      this.go('/rooms/' + room.id);
    },
    async openRoom(roomId) {
      try {
        this.currentRoom = await api('/rooms/' + roomId);
        await this.loadMessages();
        this.startPolling(roomId);
      } catch (e) {
        this.fail(e);
        if (e.status === 403) this.go('/rooms');
      }
    },
    async loadMessages(older) {
      try {
        const query = '?limit=20' + (older && this.msgCursor ? '&cursor=' + this.msgCursor : '');
        const page = await api('/rooms/' + this.currentRoom.id + '/messages' + query);
        if (older) {
          this.messages = (page.items || []).concat(this.messages);
        } else {
          this.messages = page.items || [];
        }
        this.msgCursor = page.nextCursor;
      } catch (e) { this.fail(e); }
    },
    async sendMessage() {
      if (!this.msgText.trim()) return;
      try {
        await api('/rooms/' + this.currentRoom.id + '/messages', {
          method: 'POST',
          body: { content: this.msgText, msgType: 1 }
        });
        this.msgText = '';
        await this.loadMessages();
      } catch (e) { this.fail(e); }
    },
    startPolling(roomId) {
      this.stopPolling();
      this.timer = setInterval(async () => {
        if (this.route.name !== 'chat') return;
        try {
          const page = await api('/rooms/' + roomId + '/messages?limit=20');
          this.messages = page.items || [];
        } catch (e) { /* 轮询失败静默处理 */ }
      }, 4000);
    },
    stopPolling() {
      if (this.timer) { clearInterval(this.timer); this.timer = null; }
    },

    /* ---------------------------------------------------------- 博客 */
    async loadPosts() {
      try {
        const params = new URLSearchParams();
        if (this.filter.boardId) params.set('boardId', this.filter.boardId);
        if (this.filter.tagId) params.set('tagId', this.filter.tagId);
        params.set('sort', this.filter.sort || 'latest');
        this.posts = await api('/posts?' + params.toString());
      } catch (e) { this.fail(e); }
    },
    async createPost() {
      try {
        const post = await api('/posts', { method: 'POST', body: this.postForm });
        this.postDialog = false;
        this.postForm = { boardId: null, title: '', body: '', tagIds: [] };
        this.notify('发布成功' + (post.status === 1 ? '，内容进入待审' : ''));
        this.loadPosts();
      } catch (e) { this.fail(e); }
    },
    async openPost(postId) {
      try {
        this.currentPost = await api('/posts/' + postId);
        this.replies = await api('/posts/' + postId + '/replies');
        try {
          this.aiResult = await api('/posts/' + postId + '/ai-result');
        } catch (e) { this.aiResult = null; }
      } catch (e) { this.fail(e); }
    },
    async addReply() {
      if (!this.replyText.trim()) return;
      try {
        await api('/posts/' + this.currentPost.id + '/replies', {
          method: 'POST', body: { content: this.replyText }
        });
        this.replyText = '';
        this.notify('回帖成功');
        this.replies = await api('/posts/' + this.currentPost.id + '/replies');
      } catch (e) { this.fail(e); }
    },
    async toggleLike() {
      try {
        const res = await api('/posts/' + this.currentPost.id + '/like', {
          method: 'POST', body: { liked: !this.currentPost.liked }
        });
        this.currentPost.liked = res.active;
        this.currentPost.likeCount = res.count;
      } catch (e) { this.fail(e); }
    },
    async toggleFavorite() {
      try {
        const res = await api('/posts/' + this.currentPost.id + '/favorite', {
          method: 'POST', body: { liked: !this.currentPost.favorited }
        });
        this.currentPost.favorited = res.active;
        this.currentPost.favoriteCount = res.count;
      } catch (e) { this.fail(e); }
    },

    /* ---------------------------------------------------------- 检索 */
    async doSearch() {
      try {
        const params = new URLSearchParams();
        if (this.searchQ) params.set('q', this.searchQ);
        if (this.filter.tagId) params.set('tagId', this.filter.tagId);
        this.searchResults = await api('/search?' + params.toString());
      } catch (e) { this.fail(e); }
    },
    openSearchResult(item) {
      if (item.type === 'post') this.go('/posts/' + item.id);
      else this.go('/rooms/' + item.id);
    },

    /* ---------------------------------------------------------- 审核 */
    async loadPending() {
      try {
        this.pending = await api('/admin/review/tasks');
      } catch (e) {
        this.fail(e);
        if (e.status === 403) this.go('/posts');
      }
    },
    async review(item, action) {
      try {
        await api('/admin/review/' + item.postId, {
          method: 'POST',
          body: { action, remark: this.reviewRemark[item.postId] || '' }
        });
        this.notify(action === 'approve' ? '已通过' : '已删除');
        this.loadPending();
      } catch (e) { this.fail(e); }
    }
  },
  template: `
<div>
  <div class="topbar" v-if="loggedIn">
    <div class="brand">知屿校园</div>
    <div class="nav">
      <a :href="'#/posts'" :class="{active: ['posts','post'].includes(route.name)}">博客</a>
      <a :href="'#/rooms'" :class="{active: ['rooms','chat'].includes(route.name)}">聊天室</a>
      <a :href="'#/search'" :class="{active: route.name === 'search'}">检索</a>
      <a v-if="isAdmin" :href="'#/review'" :class="{active: route.name === 'review'}">审核台</a>
    </div>
    <div class="who">
      <span>{{ state.user ? state.user.nickname : '' }}
        <el-tag size="small" v-if="isAdmin" type="danger">管理员</el-tag>
      </span>
      <el-button size="small" @click="logout">退出</el-button>
    </div>
  </div>

  <!-- 登录 -->
  <div class="center-box" v-if="route.name === 'login'">
    <div class="login-card">
      <h1>知屿校园</h1>
      <div class="tip">校园信息智能平台 · 需求分析课程设计</div>
      <el-tabs v-model="tab">
        <el-tab-pane label="登录" name="login">
          <el-form label-position="top">
            <el-form-item label="学号 / 工号">
              <el-input v-model="loginForm.account" placeholder="如 20230001" />
            </el-form-item>
            <el-form-item label="口令">
              <el-input v-model="loginForm.password" type="password" show-password
                        @keyup.enter="doLogin" />
            </el-form-item>
            <el-button type="primary" style="width:100%" @click="doLogin">登录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form label-position="top">
            <el-form-item label="学号 / 工号">
              <el-input v-model="loginForm.account" placeholder="4~32 位字母或数字" />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="loginForm.nickname" />
            </el-form-item>
            <el-form-item label="口令">
              <el-input v-model="loginForm.password" type="password" show-password
                        placeholder="至少 8 位，含字母和数字" />
            </el-form-item>
            <el-button type="primary" style="width:100%" @click="doRegister">注册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>

  <div class="page" v-else>
    <!-- 聊天室列表 -->
    <div v-if="route.name === 'rooms'">
      <div class="card">
        <div class="row">
          <h2 class="grow">聊天室</h2>
          <el-button type="primary" @click="roomDialog = true">创建聊天室</el-button>
        </div>
        <div class="sub">按标签筛选，点击进入聊天</div>
        <div class="row" style="margin-bottom:14px">
          <el-select v-model="filter.tagId" placeholder="全部标签" clearable style="width:200px"
                     @change="loadRooms">
            <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </div>
        <el-empty v-if="rooms.length === 0" description="还没有聊天室，创建一个吧" />
        <div v-for="r in rooms" :key="r.id" class="row"
             style="padding:12px 0;border-bottom:1px solid #eef1f6">
          <div class="grow">
            <div style="font-weight:600">{{ r.name }}</div>
            <div class="muted">{{ r.intro }} · {{ r.memberCount }} 人</div>
            <el-tag v-for="t in r.tags" :key="t" size="small" style="margin-right:6px">{{ t }}</el-tag>
          </div>
          <el-button size="small" @click="joinRoom(r)">进入</el-button>
        </div>
      </div>
    </div>

    <!-- 聊天界面 -->
    <div v-if="route.name === 'chat' && currentRoom">
      <div class="card">
        <div class="row">
          <h2 class="grow">{{ currentRoom.name }}</h2>
          <el-button size="small" @click="go('/rooms')">返回列表</el-button>
        </div>
        <div class="sub">{{ currentRoom.intro }} · {{ currentRoom.memberCount }} 人</div>
        <div class="msg-list">
          <el-empty v-if="messages.length === 0" description="还没有消息，说点什么" />
          <div class="msg" v-for="m in messages" :key="m.id">
            <div class="who">{{ m.senderNickname }}</div>
            <div class="bubble">{{ m.content }}</div>
          </div>
        </div>
        <div class="row" style="margin-top:12px">
          <el-input class="grow" v-model="msgText" placeholder="说点什么…（Enter 发送）"
                    @keyup.enter="sendMessage" />
          <el-button type="primary" @click="sendMessage">发送</el-button>
        </div>
      </div>
    </div>

    <!-- 帖子列表 -->
    <div v-if="route.name === 'posts'">
      <div class="card">
        <div class="row">
          <h2 class="grow">博客</h2>
          <el-button type="primary" @click="postDialog = true">发帖</el-button>
        </div>
        <div class="row" style="margin:12px 0">
          <el-select v-model="filter.boardId" placeholder="全部板块" clearable style="width:160px"
                     @change="loadPosts">
            <el-option v-for="b in boards" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
          <el-select v-model="filter.tagId" placeholder="全部标签" clearable style="width:160px"
                     @change="loadPosts">
            <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
          <el-radio-group v-model="filter.sort" @change="loadPosts">
            <el-radio-button label="latest">最新</el-radio-button>
            <el-radio-button label="hot">最热</el-radio-button>
          </el-radio-group>
        </div>
        <el-empty v-if="posts.length === 0" description="还没有帖子" />
        <div v-for="p in posts" :key="p.id" style="padding:12px 0;border-bottom:1px solid #eef1f6">
          <div class="post-title" @click="go('/posts/' + p.id)">{{ p.title }}</div>
          <div class="muted" style="margin:4px 0">{{ p.excerpt }}</div>
          <div class="row">
            <el-tag v-for="t in p.tags" :key="t" size="small">{{ t }}</el-tag>
            <span class="muted">{{ p.authorNickname }} · {{ p.boardName }} ·
              浏览 {{ p.viewCount }} · 赞 {{ p.likeCount }} · 收藏 {{ p.favoriteCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 帖子详情 -->
    <div v-if="route.name === 'post' && currentPost">
      <div class="card">
        <h2>{{ currentPost.title }}</h2>
        <div class="muted" style="margin:6px 0 14px">
          {{ currentPost.authorNickname }} · {{ currentPost.boardName }} ·
          浏览 {{ currentPost.viewCount }}
        </div>
        <div style="line-height:1.9;white-space:pre-wrap">{{ currentPost.body }}</div>
        <div class="row" style="margin-top:16px">
          <el-button :type="currentPost.liked ? 'danger' : 'default'" @click="toggleLike">
            赞 {{ currentPost.likeCount }}
          </el-button>
          <el-button :type="currentPost.favorited ? 'warning' : 'default'" @click="toggleFavorite">
            收藏 {{ currentPost.favoriteCount }}
          </el-button>
          <el-button @click="go('/posts')">返回</el-button>
        </div>
        <div v-if="aiResult" class="ai-panel" style="margin-top:16px">
          <b>AI 处理结果</b>（置信度 {{ aiResult.confidence }}，
          {{ aiResult.violation ? '判定可能存在违规' : '未发现违规' }}）
          <div>摘要：{{ aiResult.summary }}</div>
          <div>
            自动标签：
            <el-tag v-for="t in aiResult.tags" :key="t.tagId" size="small"
                    style="margin-right:6px">{{ t.name }}</el-tag>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>回帖（{{ replies.length }}）</h2>
        <div v-for="r in replies" :key="r.id" style="padding:10px 0;border-bottom:1px solid #eef1f6">
          <div class="muted">{{ r.authorNickname }}</div>
          <div>{{ r.content }}</div>
        </div>
        <div class="row" style="margin-top:12px">
          <el-input class="grow" v-model="replyText" placeholder="写下你的回帖"
                    @keyup.enter="addReply" />
          <el-button type="primary" @click="addReply">回帖</el-button>
        </div>
      </div>
    </div>

    <!-- 检索 -->
    <div v-if="route.name === 'search'">
      <div class="card">
        <h2>检索</h2>
        <div class="sub">排序 = 0.5×相关度 + 0.3×热度 + 0.2×你的偏好</div>
        <div class="row" style="margin-bottom:14px">
          <el-input class="grow" v-model="searchQ" placeholder="输入关键词，如 高数"
                    @keyup.enter="doSearch" />
          <el-button type="primary" @click="doSearch">搜索</el-button>
        </div>
        <el-empty v-if="searchResults.length === 0" description="没有匹配结果" />
        <div v-for="item in searchResults" :key="item.type + item.id"
             style="padding:12px 0;border-bottom:1px solid #eef1f6">
          <div class="row">
            <span class="post-title" @click="openSearchResult(item)">{{ item.title }}</span>
            <el-tag size="small" type="info">{{ item.type === 'post' ? '帖子' : '聊天室' }}</el-tag>
            <span class="score-badge">score {{ item.score }}</span>
          </div>
          <div class="muted" style="margin:4px 0">{{ item.excerpt }}</div>
          <div class="muted">
            rel {{ item.rel }} · heat {{ item.heat }} · pref {{ item.pref }}
            <el-tag v-for="t in item.tags" :key="t" size="small" style="margin-left:6px">{{ t }}</el-tag>
          </div>
        </div>
      </div>
    </div>

    <!-- 审核台 -->
    <div v-if="route.name === 'review'">
      <div class="card">
        <h2>审核台</h2>
        <div class="sub">只处理待审内容；删除与恢复都会记录处置人</div>
        <el-empty v-if="pending.length === 0" description="没有待审内容" />
        <div v-for="item in pending" :key="item.postId"
             style="padding:14px 0;border-bottom:1px solid #eef1f6">
          <div style="font-weight:600">{{ item.title }}</div>
          <div class="muted" style="margin:4px 0">{{ item.excerpt }}</div>
          <div class="muted">
            作者 {{ item.authorNickname }} · AI 置信度 {{ item.confidence }} ·
            {{ item.violation ? '判定可能违规' : '未判定违规' }}
          </div>
          <div class="row" style="margin-top:8px">
            <el-input v-model="reviewRemark[item.postId]" placeholder="处置备注（可选）"
                      style="width:320px" />
            <el-button type="success" size="small" @click="review(item, 'approve')">通过</el-button>
            <el-button type="danger" size="small" @click="review(item, 'reject')">删除</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 创建聊天室 -->
  <el-dialog v-model="roomDialog" title="创建聊天室" width="480px">
    <el-form label-position="top">
      <el-form-item label="名称"><el-input v-model="roomForm.name" /></el-form-item>
      <el-form-item label="简介"><el-input v-model="roomForm.intro" type="textarea" /></el-form-item>
      <el-form-item label="标签">
        <el-select v-model="roomForm.tagIds" multiple style="width:100%">
          <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="roomDialog = false">取消</el-button>
      <el-button type="primary" @click="createRoom">创建</el-button>
    </template>
  </el-dialog>

  <!-- 发帖 -->
  <el-dialog v-model="postDialog" title="发帖" width="560px">
    <el-form label-position="top">
      <el-form-item label="板块">
        <el-select v-model="postForm.boardId" style="width:100%">
          <el-option v-for="b in boards" :key="b.id" :label="b.name" :value="b.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="标题"><el-input v-model="postForm.title" maxlength="100" /></el-form-item>
      <el-form-item label="正文">
        <el-input v-model="postForm.body" type="textarea" :rows="6" maxlength="20000" />
      </el-form-item>
      <el-form-item label="标签（最多 5 个）">
        <el-select v-model="postForm.tagIds" multiple style="width:100%">
          <el-option v-for="t in tags" :key="t.id" :label="t.name" :value="t.id" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="postDialog = false">取消</el-button>
      <el-button type="primary" @click="createPost">发布</el-button>
    </template>
  </el-dialog>
</div>
`
};

createApp(app).use(ElementPlus).mount('#app');
