import sys
import time

# Give vhs time to Show the screen
time.sleep(0.5)

# Clear the screen to hide the "python3 fake_shell.py" command
sys.stdout.write("\033[2J\033[H")
sys.stdout.flush()

# Show the fake prompt
sys.stdout.write("\033[1;35m>\033[0m ")
sys.stdout.flush()
time.sleep(1)

# Simulate the user typing the command
command = "/share-skills"
for char in command:
    sys.stdout.write(char)
    sys.stdout.flush()
    time.sleep(0.1)

# Simulate hitting enter
print()
time.sleep(0.5)

print("\033[1;34m# Detecting AI tools on your machine...\033[0m")
time.sleep(1)
print("  \033[1;32m✓\033[0m Claude Code      ~/.claude/skills/")
time.sleep(0.4)
print("  \033[1;32m✓\033[0m Cursor           .cursorrules")
time.sleep(0.4)
print("  \033[1;32m✓\033[0m Windsurf         ~/.codeium/windsurf/")
time.sleep(0.4)
print("  \033[1;32m✓\033[0m Cline            .clinerules")
time.sleep(0.4)
print("  \033[1;32m✓\033[0m VS Code Copilot  .github/copilot-instructions.md")
time.sleep(1)
print("")

print("\033[1;34m# Syncing 9 skills to 5 tools...\033[0m")
time.sleep(1)
print("  dev-iterate    → Claude Code, Cursor, Windsurf, Cline, VS Code")
time.sleep(0.2)
print("  test           → Claude Code, Cursor, Windsurf, Cline, VS Code")
time.sleep(0.2)
print("  commit         → Claude Code, Cursor, Windsurf, Cline, VS Code")
time.sleep(0.2)
print("  share-skills   → Claude Code, Cursor, Windsurf, Cline, VS Code")
time.sleep(0.8)
print("")

print("\033[1;34m# Done! 9 skills synced to 5 tools.\033[0m")

time.sleep(0.5)
sys.stdout.write("\033[1;35m>\033[0m ")
sys.stdout.flush()

time.sleep(5)
