
import os
import requests
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {"Accept": "application/vnd.github+json"}

if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

BASE_URL = "https://api.github.com"


# ---------- Fetch all pages from GitHub ----------
def get_all_pages(url, params=None):
    results = []
    params = dict(params or {})
    params["per_page"] = 100
    page = 1

    while True:
        params["page"] = page

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            print("GitHub API Error:", response.status_code)
            print(response.text[:500])
            return None

        data = response.json()

        if not isinstance(data, list):
            print("Unexpected GitHub API response.")
            return None

        results.extend(data)

        if len(data) < 100:
            break

        page += 1

    return results


# ---------- Fetch GitHub activity ----------
def get_github_data(username):
    repo_url = f"{BASE_URL}/users/{username}/repos"

    repos = get_all_pages(
        repo_url,
        {"type": "owner", "sort": "updated"}
    )

    if repos is None:
        return None

    repo_count = len(repos)
    total_commits = 0
    last_commit_date = None
    repo_details = []

    for repo in repos:
        repo_name = repo["name"]
        owner = repo["owner"]["login"]

        commits_url = (
            f"{BASE_URL}/repos/{owner}/{repo_name}/commits"
        )

        # Count commits authored by or committed by the user
        commits = get_all_pages(
            commits_url,
            {"author": username}
        )

        if commits is None:
            continue

        commit_count = len(commits)
        total_commits += commit_count

        for item in commits:
            commit = item.get("commit", {})
            author = commit.get("author") or {}
            committer = commit.get("committer") or {}

            commit_date = (
                author.get("date") or committer.get("date")
            )

            if commit_date and (
                last_commit_date is None
                or commit_date > last_commit_date
            ):
                last_commit_date = commit_date

        repo_details.append({
            "name": repo_name,
            "commits": commit_count
        })

    return (
        repo_count,
        total_commits,
        last_commit_date,
        repo_details
    )


# ---------- Create PDF report ----------
def create_pdf(
    username,
    repo_count,
    total_commits,
    last_commit,
    repo_details
):
    file_name = f"{username}_GitHub_Report.pdf"
    pdf = canvas.Canvas(file_name, pagesize=letter)

    def draw_header():
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(
            30, 750,
            f"GitHub Activity Report for {username}"
        )

        pdf.setFont("Helvetica", 12)
        pdf.drawString(30, 720, f"Total Repositories: {repo_count}")
        pdf.drawString(30, 700, f"Total Commits: {total_commits}")

        if last_commit:
            try:
                date = datetime.fromisoformat(
                    last_commit.replace("Z", "+00:00")
                )
                date_text = date.strftime("%d-%m-%Y %H:%M:%S UTC")
            except ValueError:
                date_text = last_commit
        else:
            date_text = "No commits found"

        pdf.drawString(30, 680, f"Latest Commit: {date_text}")
        pdf.drawString(30, 650, "Repository-wise Details:")

    draw_header()
    y = 620

    for repo in repo_details:
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 750

        pdf.drawString(
            40, y,
            f"{repo['name']} : {repo['commits']} commits"
        )
        y -= 20

    pdf.save()
    print(f"\nPDF generated: {file_name}")


# ---------- Main program ----------
if __name__ == "__main__":
    username = input("Enter GitHub Username: ").strip()

    if not username:
        print("Please enter a valid GitHub username.")
    else:
        try:
            result = get_github_data(username)

            if result is None:
                print("Could not retrieve GitHub data.")
            else:
                (
                    repo_count,
                    total_commits,
                    last_commit,
                    repo_details
                ) = result

                create_pdf(
                    username,
                    repo_count,
                    total_commits,
                    last_commit,
                    repo_details
                )

                print("\nSUMMARY")
                print("----------------------------------")
                print("Username:", username)
                print("Repositories:", repo_count)
                print("Total Commits:", total_commits)
                print("Last Commit:", last_commit)

                print("\nRepository Details:")
                for repo in repo_details:
                    print(
                        f"{repo['name']} : "
                        f"{repo['commits']} commits"
                    )

                print("\nPDF created successfully!")

        except requests.exceptions.RequestException as error:
            print("Network error:", error)
