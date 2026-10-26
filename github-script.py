import subprocess
import sys
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

def get_commit_message(auto_mode):
    if auto_mode:
        return "fixed some bugs"
    else:
        return input("=> ")

def check_git_result(result, command_name):
    if result.returncode == 0:
        print(f"git {command_name} is successful!")
    else:
        print(f"git {command_name} has failed.")
        print(f"Details: {result.stderr.strip()}")
        sys.exit(1)

# pwdfoldr = subprocess.run(["pwd"], capture_output=True, text=True).stdout.strip()
# ezafoldr = subprocess.run(["eza"], capture_output=True, text=True).stdout.strip()
pwdfoldr = run_command(["pwd"]).stdout.strip()
ezafoldr = run_command(["eza"]).stdout.strip()
print(f"used folder: n\
        {pwdfoldr}")
print(f"eza of folder: n\
        {ezafoldr}")

# GIT ADD
print("proceed?")
if args.auto or input("Y/N => ").strip().upper() == "Y":
    print("starting to add...")
    
    git_add_result = run_command(["git", "add", "."])
    check_git_result(git_add_result, "add")
    
    # GIT COMMIT
    print("continuing!")
    commit_msg = get_commit_message(args.auto)

    git_commit_result = run_command(["git", "commit", "-m", commit_msg])
    check_git_result(git_commit_result, "commit")
    
    # GIT PUSHING
    print("continuing!")
    print("pushing...")

    git_push_result = run_command(["git", "push", "-u", "origin", "main"])
    
    check_git_result(git_push_result, "push")
    notify = run_command(["notify-send", "hallo!", "pushing is complete, go check!"]) 

else:
    print("then go fuck urself")
    sys.exit(1)

