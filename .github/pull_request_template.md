## 何を変えたか

<!-- 変更の理由と中身。plugins/ を触ったら version を上げたことも書く -->

## 出す前の確認

- [ ] `git config core.hooksPath` が `hooks` を返す（ローカル pre-push が有効。**Owner も省略しない**）
- [ ] `python3 hooks/check_secrets.py --all` が手元で ✓
- [ ] 個人名・クライアント名・報酬・評価・鍵を入れていない（CONTRIBUTING.md 0章）
- [ ] `plugins/` を触った場合、`plugin.json` と `marketplace.json` の version を両方上げた
- [ ] Skill を足した場合: 誰が使うか（関門1）と、自分で1回動かした出力（関門4）を「何を変えたか」に貼った（CONTRIBUTING.md 3章・9章）
- [ ] Skill・コマンドを足した場合: `/hicard:skill-review` の結果の表を「何を変えたか」に貼った（落とすが0件）
