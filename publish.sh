#!/usr/bin/env bash
# =============================================================================
#  一键发布到 GitHub Pages
#  用法：  bash publish.sh <GitHub用户名> [仓库名]
#  示例：  bash publish.sh zhangqing
#          bash publish.sh zhangqing job-market-analysis
#
#  前置条件：在 GitHub 网页上先建好一个**空仓库**（不要勾选 README/.gitignore/LICENSE）
# =============================================================================
set -uo pipefail

GH_USER="${1:-}"
REPO="${2:-job-market-analysis}"

if [ -z "$GH_USER" ]; then
  echo "用法: bash publish.sh <GitHub用户名> [仓库名，默认 job-market-analysis]"
  echo "示例: bash publish.sh zhangqing"
  exit 1
fi

cd "$(dirname "$0")" || exit 1
echo "工作目录: $(pwd)"
echo

# ---------- 1. 把 README 里的占位符换成真实用户名 ----------
if grep -q '<你的GitHub用户名>' README.md 2>/dev/null; then
  sed -i "s/<你的GitHub用户名>/${GH_USER}/g" README.md
  echo "[1/5] README 在线链接已指向 https://${GH_USER}.github.io/${REPO}/"
else
  echo "[1/5] README 占位符已替换过，跳过"
fi

# 若用了自定义仓库名，同步修正 README 里的 Pages 地址与目录树标签
if [ "$REPO" != "job-market-analysis" ]; then
  sed -i "s|github.io/job-market-analysis|github.io/${REPO}|g" README.md
  sed -i "s|^job-market-analysis/$|${REPO}/|" README.md
  echo "      README 内的仓库名已同步为 ${REPO}"
fi

# ---------- 2. 提交身份（只写入本仓库，不动全局配置） ----------
if [ -z "$(git config user.name)" ]; then
  read -r -p "提交显示的名字（建议填真名，会出现在 GitHub commit 记录里）: " GNAME
  git config user.name "$GNAME"
fi
if [ -z "$(git config user.email)" ]; then
  read -r -p "提交显示的邮箱（填 GitHub 账号邮箱，否则提交不会关联到你的头像）: " GMAIL
  git config user.email "$GMAIL"
fi
echo "[2/5] 提交身份: $(git config user.name) <$(git config user.email)>"

# ---------- 3. 首次提交 ----------
git add -A
if git diff --cached --quiet; then
  echo "[3/5] 没有新改动，跳过提交"
else
  git commit -q -m "feat: 大数据招聘岗位数据分析项目（求职作品集）" && \
  echo "[3/5] 已提交: $(git log -1 --pretty='%h %s')"
fi

# ---------- 4. 绑定远程仓库 ----------
REMOTE="https://github.com/${GH_USER}/${REPO}.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE"
else
  git remote add origin "$REMOTE"
fi
echo "[4/5] 远程仓库: $REMOTE"

# ---------- 5. 推送 ----------
echo "[5/5] 开始推送（首次会弹出浏览器让你登录 GitHub，按提示授权即可）..."
echo
if git push -u origin main; then
  echo
  echo "=============================================================="
  echo "  推送成功！"
  echo "=============================================================="
  echo
  echo "最后一步（只需做一次，约 1 分钟生效）："
  echo "  1. 打开 https://github.com/${GH_USER}/${REPO}/settings/pages"
  echo "  2. Source 选择  Deploy from a branch"
  echo "  3. Branch 选  main ，目录选  / (root) ，点 Save"
  echo "  4. 等 1-2 分钟，访问下面的地址："
  echo
  echo "     可视化总览   https://${GH_USER}.github.io/${REPO}/"
  echo "     完整报告     https://${GH_USER}.github.io/${REPO}/report.html"
  echo
  echo "  仓库首页     https://github.com/${GH_USER}/${REPO}"
  echo
else
  echo
  echo "=============================================================="
  echo "  推送失败，最常见的原因有三个："
  echo "=============================================================="
  echo "  1) 远程仓库还不存在 —— 先去建一个空仓库（务必不勾选任何初始化文件）："
  echo "     https://github.com/new  仓库名填 ${REPO}"
  echo
  echo "  2) 认证失败 —— 在终端重新执行一次，登录弹窗里选浏览器授权"
  echo
  echo "  3) 仓库已存在且非空 —— 执行下面命令后再试："
  echo "     git pull --rebase origin main"
  echo
  exit 1
fi
