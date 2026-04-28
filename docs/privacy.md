# Privacy

Agent Interview Coach is local-first, but model calls still send selected context to your configured model API provider.

## What Stays Local

- Raw resume/project files in `app/resume_materials/` or your imported folder.
- Session state in `app/sessions.json`.
- Corpus cache in `app/interview_corpus_cache.json`.
- Reviews in `app/reviews/`.
- Answer drafts in `app/answers/`.
- WeChat credentials stored by `wechat-clawbot`.

## What Is Sent to the Model API

For each interview turn, the app sends:

- The current user message.
- Recent conversation history.
- Selected chunks from the imported resume/project materials.
- Interview stage/mode instructions and tracked weaknesses.

When running `/生成背景`, the app sends a larger summary-sized selection of the imported materials to generate `AI面试背景材料.generated.md`.

## What Not to Commit

Never commit:

- `.env`
- `sessions.json`
- `interview_corpus_cache.json`
- `reviews/`
- `answers/`
- `resume_materials/`
- WeChat credential files
- API keys or tokens
- Real resumes, certificates, screenshots, or project documents

The included `.gitignore` excludes these by default.

## Deleting Local Data

Stop the bot first, then delete any of:

```text
app/sessions.json
app/interview_corpus_cache.json
app/reviews/
app/answers/
app/resume_materials/
app/AI面试背景材料.generated.md
```

To remove WeChat credentials, inspect the `wechat-clawbot` credential path shown by:

```powershell
python app\smoke_test.py --wechat
```
