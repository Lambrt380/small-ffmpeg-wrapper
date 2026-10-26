import subprocess
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--auto", action="store_true")
args = parser.parse_args()

if args.auto:
    print("----- RUNNING IN AUTO-MODE -------")
else:
    print("running...")

def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    return result

# pwdfoldr = subprocess.run(["pwd"], capture_output=True, text=True).stdout.strip()
# ezafoldr = subprocess.run(["eza"], capture_output=True, text=True).stdout.strip()
pwdfoldr = run_command(["pwd"]).stdout.strip()
ezafoldr = run_command(["eza"]).stdout.strip()
print(f"used folder: {pwdfoldr}")
print(f"eza of folder: {ezafoldr}")

print("proceed?")
if args.auto or input("Y/N => ").strip().upper() == "Y":
    print("starting to add...")
    
    git_add_result = run_command(["git", "add", "."])
    
    if git_add_result.returncode == 0:
        print("git add is succesful!")
    else:
        print("git add . has failed!")
        print(f"Details: {git_add_result.stderr.strip()}")
        exit()
    
    print("continuing!")
    if args.auto:
        commit_msg = "fixed some bugs"
    else:    
        print("what to commit?")
        commit_msg = input("=> ")
    git_commit_result = run_command(["git", "commit", "-m", commit_msg])
    
    if git_commit_result.returncode == 0:
        print("git commit is succesful!")
    else:
        print("git commit has failed.")
        print(f"Details: {git_commit_result.stderr.strip()}")
        exit()

    print("continuing!")
    print("pushing...")

    git_push_result = run_command(["git", "push", "-u", "origin", "main"])
    
    if git_push_result.returncode == 0:
        print("git commit is succesful!")
        print(f"Details: {git_push_result.stderr.strip()}")
        notify = run_command(["notify-send", "hallo!", "pushing is complete, go check!"]) 
    else:
        print("git push has failed.")
        print(f"Details: {git_push_result.stderr.strip()}")
        exit()


