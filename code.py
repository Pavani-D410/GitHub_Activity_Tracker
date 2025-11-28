import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

# ---------- Function: Fetch GitHub data ----------
def get_github_data(username):
    base_url = f"https://api.github.com/users/{username}"

    # Get repo list
    repos = requests.get(f"{base_url}/repos").json()

    repo_count = len(repos)
    total_commits = 0
    last_commit_date = None

    repo_details = []

    for repo in repos:
        repo_name = repo['name']

        commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
        commit_data = requests.get(commits_url).json()

        commit_count = len(commit_data)

        # Update total commits
        total_commits += commit_count

        # Find last commit date
        if commit_count > 0:
            recent = commit_data[0]['commit']['author']['date']
            if last_commit_date is None or recent > last_commit_date:
                last_commit_date = recent

        # Store repo info
        repo_details.append({
            "name": repo_name,
            "commits": commit_count
        })

    return repo_count, total_commits, last_commit_date, repo_details

# ---------- Function: Create PDF ----------
def create_pdf(username, repo_count, total_commits, last_commit, repo_details):
    file_name = f"{username}_GitHub_Report.pdf"
    pdf = canvas.Canvas(file_name, pagesize=letter)

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(30, 750, f"GitHub Activity Report for {username}")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(30, 720, f"Total Repositories: {repo_count}")
    pdf.drawString(30, 700, f"Total Commits: {total_commits}")

    if last_commit:
        formatted_date = datetime.strptime(last_commit, "%Y-%m-%dT%H:%M:%SZ")
        pdf.drawString(30, 680, f"Last Commit Date: {formatted_date}")
    else:
        pdf.drawString(30, 680, f"Last Commit Date: No commits found")

    pdf.drawString(30, 650, "Repository-wise Details:")

    y = 630
    for repo in repo_details:
        pdf.drawString(40, y, f"- {repo['name']} : {repo['commits']} commits")
        y -= 20
        if y < 50:  # new page if necessary
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 750

    pdf.save()
    print(f"\nPDF generated: {file_name}")

# ---------- MAIN PROGRAM ----------
username = input("Enter GitHub Username: ")

repo_count, total_commits, last_commit, repo_details = get_github_data(username)
create_pdf(username, repo_count, total_commits, last_commit, repo_details)

print("\nSUMMARY")
print("----------------------------------")
print("Username:", username)
print("Repositories:", repo_count)
print("Total Commits:", total_commits)
print("Last Commit:", last_commit)
print("PDF created successfully!")
