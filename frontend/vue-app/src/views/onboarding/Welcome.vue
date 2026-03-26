<template>
  <div class="step">
    <div class="logo">MultiYou</div>
    <h1>创建属于你的 AI 分身</h1>
    <p>上传一张照片，配置 AI 模型，让专属分身代替你与世界对话。</p>
    <ul class="features">
      <li>🎨 像素风格头像，独特可爱</li>
      <li>🤖 支持 DeepSeek、Ollama 等多种模型</li>
      <li>💬 多会话管理，随时切换</li>
    </ul>
    <div class="actions">
      <router-link to="/login" class="btn-ghost">已有账号，去登录</router-link>
      <router-link to="/onboarding/account" class="btn-primary">开始使用 →</router-link>
    </div>
  </div>
</template>

<style scoped>
.step { text-align: center; }
.logo { font-size: 28px; font-weight: 700; color: #7c6fff; margin-bottom: 16px; }
h1 { font-size: 22px; margin-bottom: 12px; }
p { color: #888; margin-bottom: 24px; }
.features { list-style: none; text-align: left; display: inline-block; margin-bottom: 32px; }
.features li { padding: 6px 0; color: #aaa; font-size: 14px; }
.actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.btn-primary {
  padding: 12px 24px;
  background: #7c6fff;
  color: #fff;
  border-radius: 6px;
  font-size: 15px;
  text-decoration: none;
}
.btn-ghost {
  padding: 12px 24px;
  border: 1px solid #555;
  color: #aaa;
  border-radius: 6px;
  font-size: 15px;
  text-decoration: none;
}
</style>
