
<a id=""></a>

## **Contents**

- [Overview `⇧`](#overview-)
- [Key Features `⇧`](#key-features-)
- [Architecture `⇧`](#architecture-)
- [Deployment `⇧`](#deployment-)
- [Environment setup `⇧`](#environment-setup-)
- [Use Cases `⇧`](#use-cases-)

<a id="conventions-"></a>


# Overview [`⇧`](#contents)

# Key Features [`⇧`](#contents)


# Architecture [`⇧`](#contents)


# Deployment [`⇧`](#contents)


# Environment setup [`⇧`](#contents)

1. First and foremost, please see the suggested IDE setup in the dropdown below to make sure that your editor is ready for development.

> [!IMPORTANT]
>
> <details><summary>Suggested IDE setup</summary>
>
> <p>
>
> VS Code
>
> Install the following extensions:
>
> - [charliermarsh.ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
> - [streetsidesoftware.code-spell-checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)
>
> </p>
> </details>

1. [Fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) the [AI-Legal-Checker repo](https://github.com/activist-org/AI-Legal-Checker), clone your fork, and configure the remotes:

> [!NOTE]
>
> <details><summary>Consider using SSH</summary>
>
> <p>
>
> Alternatively to using HTTPS as in the instructions below, consider SSH to interact with GitHub from the terminal. SSH allows you to connect without a user-pass authentication flow.
>
> To run git commands with SSH, remember then to substitute the HTTPS URL, `https://github.com/...`, with the SSH one, `git@github.com:...`.
>
> - e.g. Cloning now becomes `git clone git@github.com:<your-username>/AI-Legal-Checker.git`
>
> GitHub also has their documentation on how to [Generate a new SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) 🔑
>
> </p>
> </details>

```bash
# Clone your fork of the repo into the current directory.
git clone https://github.com/<your-username>/AI-Legal-Checker
# Navigate to the newly cloned directory.
cd AI-Legal-Checker
# Assign the original repo to a remote called "upstream".
git remote add upstream https://github.com/activist-org/AI-Legal-Checker
```

- Now, if you run `git remote -v` you should see two remote repositories named:
  - `origin` (forked repository)
  - `upstream` (AI-Legal-Checker repository)

3. Create a virtual environment, activate it and install dependencies:

   ```bash
   # Unix or MacOS:
   python3 -m venv venv
   source venv/bin/activate

   # Windows:
   python -m venv venv
   venv\Scripts\activate.bat

   # After activating venv:
   pip install --upgrade pip
   pip install -r requirements-dev.txt

   # To install the AI-Legal-Checker for local development:
   pip install -e .
   ```

You're now ready to work on `AI-Legal-Checker`!


# Use Cases [`⇧`](#contents)


* **License**

  * MIT License.

