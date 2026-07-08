# Agent-examples
这个项目是 Agent 一些样例代码。

## 说明
代码中用到的系统/用户环境变量‌（os.getenv）：
由操作系统维护
- Windows 通过“系统属性→环境变量”设置；
- Linux/macOS 通过 shell 配置文件如 ~/.bashrc、~/.zshrc 或 /etc/environment 导出
  ~/.zshrc 内容：
  ```
  export LLM_PROVIDER="deepseek"
  export LLM_MODEL="deepseek-v4-flash"
  export DEEPSEEK_BASE_URL="https://api.deepseek.com"
  export DEEPSEEK_API_KEY="sk-[your api key]"
  ```