# AGENTS.md

Chỉ dẫn cho agent của repo này nằm ở **[`CLAUDE.md`](CLAUDE.md)** — đọc file đó trước.

Repo dùng cả Claude Code và opencode. `CLAUDE.md` là bản gốc duy nhất;
file này chỉ trỏ sang, không lặp lại nội dung, để hai bên không lệch nhau.

## Riêng cho agent không phải Claude Code

Skill có ở hai chỗ, **cùng một nội dung**:

- `.agents/skills/` — file thật, dùng chỗ này
- `.claude/skills/` — symlink tương đối trỏ sang `../../.agents/skills/*`

Trên Windows symlink cần `core.symlinks=true` + Developer Mode; nếu chúng
hiện ra thành file text chứa đường dẫn thì cứ bỏ qua và đọc `.agents/skills/`.
