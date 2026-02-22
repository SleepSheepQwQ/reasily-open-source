name: Dependency Sync Workflow
on:
  push:
    branches:
      - main
    paths:
      - ".github/workflows/action.yml"
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Dry run mode, only check without modifying the repository"
        type: boolean
        default: true
        required: false
      create_pr:
        description: "Create pull request for changes in formal mode"
        type: boolean
        default: true
        required: false
      force_update:
        description: "Force overwrite existing files even if hash matches"
        type: boolean
        default: false
        required: false

permissions:
  contents: read
  pull-requests: write

defaults:
  run:
    shell: bash
    working-directory: "${{ github.workspace }}"

jobs:
  sync-dependencies:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Checkout repository code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          clean: true
          token: "${{ secrets.GITHUB_TOKEN }}"

      - name: Pre-check environment and directory structure
        run: |
          set -euo pipefail
          IFS=$'\n\t'

          echo "==================== 环境预校验开始 ===================="
          
          REQUIRED_TOOLS=("wget" "curl" "sha256sum" "git" "mkdir" "rm" "mv" "ls" "stat" "awk" "xargs" "basename" "dirname")
          for TOOL in "${REQUIRED_TOOLS[@]}"; do
            if ! command -v "$TOOL" &> /dev/null; then
              echo "❌ 错误：缺少必要工具 $TOOL，环境不满足执行要求"
              exit 1
            fi
            echo "✅ 工具检查通过：$TOOL"
          done

          CORE_DIRS=(
            "epub-reader-light/assets/css"
            "epub-reader-light/assets/js"
            "epub-reader-light/assets/fonts"
            "epub-reader-light/assets/epubs"
          )
          for DIR in "${CORE_DIRS[@]}"; do
            if [ ! -d "$DIR" ]; then
              echo "⚠️  目录不存在，自动创建：$DIR"
              mkdir -p "$DIR"
            fi
            echo "✅ 目录检查通过：$DIR"
          done

          git config --global core.autocrlf false
          git config --global core.fileMode false
          git config --global core.quotepath off
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"

          git pull origin main --rebase

          echo "==================== 环境预校验全部通过 ===================="

      - name: Load dependency configuration
        id: load-config
        run: |
          set -euo pipefail
          IFS=$'\n\t'

          cat > .deps_list << 'EOF'
          epub.js|0.3.93|https://cdn.jsdelivr.net/npm/epubjs@0.3.93/dist/epub.min.js|epub-reader-light/assets/js/epub.min.js|f09d7e8a99b693a71c0b1a2d4586f9c2b3d78e9f0a1b2c3d4e5f6a7b8c9d0e1
          EOF

          grep -v '^#' .deps_list | grep -v '^$' > .valid_deps
          DEP_COUNT=$(wc -l < .valid_deps)
          echo "✅ 加载有效依赖配置：$DEP_COUNT 个"
          echo "dep_count=$DEP_COUNT" >> "$GITHUB_OUTPUT"

      - name: Download and verify dependencies
        id: download-deps
        run: |
          set -euo pipefail
          IFS=$'\n\t'

          echo "==================== 依赖拉取开始 ===================="
          TMP_DIR="./.tmp_deps_download"
          mkdir -p "$TMP_DIR"
          CHANGE_LOG="./.change_log.md"
          echo "# Dependency Sync Change Log" > "$CHANGE_LOG"
          echo "Run time: $(date '+%Y-%m-%d %H:%M:%S')" >> "$CHANGE_LOG"
          echo "Triggered by: ${{ github.actor }}" >> "$CHANGE_LOG"
          echo "" >> "$CHANGE_LOG"
          echo "| Name | Version | Change Type | Target Path | Status |" >> "$CHANGE_LOG"
          echo "| ---- | ------- | ----------- | ----------- | ------ |" >> "$CHANGE_LOG"

          HAS_CHANGE=false
          FORCE_UPDATE="${{ inputs.force_update || 'false' }}"

          while IFS='|' read -r NAME VERSION URL TARGET_PATH EXPECTED_SHA; do
            NAME=$(echo "$NAME" | xargs)
            VERSION=$(echo "$VERSION" | xargs)
            URL=$(echo "$URL" | xargs)
            TARGET_PATH=$(echo "$TARGET_PATH" | xargs)
            EXPECTED_SHA=$(echo "$EXPECTED_SHA" | xargs)

            echo ""
            echo "==================== 处理依赖：$NAME v$VERSION ===================="

            TARGET_DIR=$(dirname "$TARGET_PATH")
            mkdir -p "$TARGET_DIR"

            CURRENT_SHA=""
            if [ -f "$TARGET_PATH" ]; then
              CURRENT_SHA=$(sha256sum "$TARGET_PATH" | awk '{print $1}')
              if [ "$CURRENT_SHA" == "$EXPECTED_SHA" ] && [ "$FORCE_UPDATE" != "true" ]; then
                echo "✅ 文件已存在且哈希匹配，跳过处理：$TARGET_PATH"
                echo "| $NAME | $VERSION | No Change | $TARGET_PATH | Pass |" >> "$CHANGE_LOG"
                continue
              fi
            fi

            TMP_FILE="$TMP_DIR/$(basename "$TARGET_PATH")"
            echo "📥 开始下载：$URL"
            if ! wget --tries=3 --wait=5 --timeout=10 -O "$TMP_FILE" "$URL"; then
              echo "❌ 下载失败：$NAME v$VERSION，网络异常或地址无效"
              exit 1
            fi

            FILE_SIZE=$(stat -c%s "$TMP_FILE")
            if [ "$FILE_SIZE" -lt 1024 ]; then
              echo "❌ 文件异常：$NAME v$VERSION，文件大小仅 $FILE_SIZE 字节，小于1KB最小阈值"
              exit 1
            fi

            ACTUAL_SHA=$(sha256sum "$TMP_FILE" | awk '{print $1}')
            if [ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]; then
              echo "❌ 哈希校验失败：$NAME v$VERSION"
              echo "   期望哈希：$EXPECTED_SHA"
              echo "   实际哈希：$ACTUAL_SHA"
              echo "   请检查下载地址是否正确，或更新配置中的哈希值"
              exit 1
            fi

            if [ "${{ inputs.dry_run }}" != "true" ]; then
              mv -f "$TMP_FILE" "$TARGET_PATH"
              echo "✅ 依赖处理完成：$NAME v$VERSION -> $TARGET_PATH"
            else
              echo "✅ 预校验通过，文件未写入（dry run模式）：$NAME v$VERSION"
            fi

            if [ -z "${CURRENT_SHA:-}" ]; then
              CHANGE_TYPE="New"
            else
              CHANGE_TYPE="Update"
            fi
            echo "| $NAME | $VERSION | $CHANGE_TYPE | $TARGET_PATH | Pass |" >> "$CHANGE_LOG"
            HAS_CHANGE=true

          done < .valid_deps

          echo "has_change=$HAS_CHANGE" >> "$GITHUB_OUTPUT"
          echo "change_log_path=$CHANGE_LOG" >> "$GITHUB_OUTPUT"
          echo "tmp_dir=$TMP_DIR" >> "$GITHUB_OUTPUT"

          echo ""
          echo "==================== 依赖拉取全部完成 ===================="
          if [ "$HAS_CHANGE" == "true" ]; then
            echo "ℹ️  本次执行有变更，详情见变更报告"
            cat "$CHANGE_LOG"
          else
            echo "ℹ️  本次执行无任何变更，所有依赖均已为最新正确版本"
          fi

      - name: Dry run result output
        if: inputs.dry_run == true
        run: |
          set -euo pipefail
          echo "==================== 预校验预览执行完成 ===================="
          echo "✅ 所有依赖校验通过，无执行错误"
          echo "ℹ️  本次为预校验预览模式，未对仓库进行任何修改"
          echo "ℹ️  如需正式执行，请关闭「dry_run」选项重新触发"
          echo ""
          echo "===== 变更预览 ====="
          cat "${{ steps.download-deps.outputs.change_log_path }}"

      - name: Create change branch
        if: inputs.dry_run == false && steps.download-deps.outputs.has_change == 'true'
        id: create-branch
        run: |
          set -euo pipefail
          BRANCH_NAME="auto-update-deps/$(date '+%Y%m%d-%H%M%S')"
          echo "branch_name=$BRANCH_NAME" >> "$GITHUB_OUTPUT"
          
          git checkout -b "$BRANCH_NAME"
          git add epub-reader-light/assets/
          git commit -m "chore: auto update open source dependencies [$(date '+%Y-%m-%d %H:%M')]"
          echo "✅ 变更已提交到临时分支：$BRANCH_NAME"

      - name: Create pull request
        if: inputs.dry_run == false && inputs.create_pr == true && steps.download-deps.outputs.has_change == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          token: "${{ secrets.GITHUB_TOKEN }}"
          branch: "${{ steps.create-branch.outputs.branch_name }}"
          base: main
          title: "chore: auto update open source dependencies [$(date '+%Y-%m-%d')]"
          body-path: "${{ steps.download-deps.outputs.change_log_path }}"
          labels: |
            dependencies
            automated
          delete-branch: true

      - name: Clean temporary files
        if: always()
        run: |
          rm -rf .tmp_* .deps_list .valid_deps .change_log.md ./.tmp_deps_download
          echo "✅ 临时文件清理完成"

      - name: Final result summary
        run: |
          echo "==================== 工作流执行完成 ===================="
          if [ "${{ inputs.dry_run }}" == "true" ]; then
            echo "✅ 预校验模式执行成功，无错误"
          else
            if [ "${{ steps.download-deps.outputs.has_change }}" == "true" ]; then
              echo "✅ 正式模式执行成功"
              if [ "${{ inputs.create_pr }}" == "true" ]; then
                echo "✅ PR已创建，请前往仓库审核合并"
              else
                echo "✅ 变更已提交到临时分支，未创建PR"
              fi
            else
              echo "✅ 执行成功，无依赖变更需要处理"
            fi
          fi
