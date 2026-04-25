# Terraform GitHub Repository Manager

> Manages all **github.com/amar-python** repositories as Infrastructure as Code using Terraform and the official GitHub provider.

---

## What This Does

- Creates and configures GitHub repositories declaratively
- Applies topics, descriptions, and settings automatically
- Prevents accidental deletion with lifecycle guards
- All repo config lives in one place — `variables.tf`

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Terraform | >= 1.5.0 | [developer.hashicorp.com/terraform](https://developer.hashicorp.com/terraform/install) |
| GitHub PAT | — | [github.com/settings/tokens](https://github.com/settings/tokens) (scope: `repo`) |

---

## Quick Start

### 1. Clone and enter the directory

```bash
git clone https://github.com/amar-python/terraform-github-repos.git
cd terraform-github-repos
```

### 2. Set your GitHub token as an environment variable

```bash
# Mac / Linux / Git Bash on Windows
export TF_VAR_github_token="ghp_yourtoken"

# PowerShell on Windows
$env:TF_VAR_github_token="ghp_yourtoken"
```

### 3. Initialise Terraform

```bash
terraform init
```

### 4. Preview changes

```bash
terraform plan
```

### 5. Apply changes

```bash
terraform apply
```

Type `yes` when prompted. Terraform will create/update all repositories.

---

## How to Add a New Repository

**Step 1** — Add it to `variables.tf` under `repos`:

```hcl
"MyNewProject" = {
  description = "Description of my new project"
  visibility  = "public"
  topics      = ["python", "automation", "devops"]
}
```

**Step 2** — Add a resource block in `main.tf`:

```hcl
resource "github_repository" "my_new_project" {
  name        = "MyNewProject"
  description = var.repos["MyNewProject"].description
  visibility  = var.repos["MyNewProject"].visibility
  has_issues  = true
  auto_init   = false
  lifecycle { prevent_destroy = true }
}

resource "github_repository_topics" "my_new_project" {
  repository = github_repository.my_new_project.name
  topics     = var.repos["MyNewProject"].topics
}
```

**Step 3** — Add the URL to `outputs.tf`:

```hcl
MyNewProject = github_repository.my_new_project.html_url
```

**Step 4** — Apply:

```bash
terraform plan   # preview
terraform apply  # create
```

---

## Managed Repositories

| Repository | Visibility | Description |
|---|---|---|
| [PostgreDataMigrationApp](https://github.com/amar-python/PostgreDataMigrationApp) | Public | Parameterised PostgreSQL T&E database framework |

---

## File Structure

```
terraform-github-repos/
├── main.tf                   ← Provider + repository resources
├── variables.tf              ← All repo config (edit here to add repos)
├── outputs.tf                ← URLs printed after apply
├── terraform.tfvars.example  ← Safe token template (copy → terraform.tfvars)
├── .gitignore                ← Excludes state files and secrets
└── README.md
```

---

## Security Notes

- **Never commit `terraform.tfvars`** — it's in `.gitignore`
- Always pass the token via `TF_VAR_github_token` environment variable
- The `sensitive = true` flag on the token variable prevents it appearing in `terraform plan` output
- `prevent_destroy = true` on each repo stops `terraform destroy` from deleting your repositories accidentally

---

## Useful Commands

```bash
terraform init      # download provider plugins (run once)
terraform plan      # preview what will change
terraform apply     # apply changes to GitHub
terraform show      # show current state
terraform output    # print repository URLs
```
