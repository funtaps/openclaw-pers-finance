# TOOLS.md - Local Notes

## Sending Media to Telegram

**CRITICAL:** Never include MEDIA: paths in regular reply text - they won't render as images.

To send images/files to the user:
1. Use the `message` tool with `action=send`
2. Set `media` parameter to the file path
3. Optionally add `caption` for context
4. Reply with `NO_REPLY` to avoid duplicate messages

Example:
```
message(action=send, channel=telegram, target=<chat-id>, media=/path/to/image.jpg, caption="Description")
```

**Wrong:** Including `MEDIA:/path/to/image.jpg` in reply text
**Right:** Using message tool with media parameter

---

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
