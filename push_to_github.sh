#!/bin/bash
# Script to push code to GitHub

echo "═══════════════════════════════════════════════════════════════"
echo "           Pushing to GitHub"
echo "═══════════════════════════════════════════════════════════════"
echo ""

cd /Users/adarshvuppala/kg_demo

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "📋 Setting up remote..."
    git remote add origin https://github.com/adarshvuppala-nu/kg_demo.git
fi

echo "📋 Current remote:"
git remote -v
echo ""

echo "📋 Current branch:"
git branch
echo ""

echo "📋 Status:"
git status --short | head -10
echo ""

echo "🚀 Attempting to push..."
echo "   (You may need to authenticate with GitHub)"
echo ""

git push -u origin main 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "   Repository: https://github.com/adarshvuppala-nu/kg_demo.git"
else
    echo ""
    echo "⚠️  Push failed. Common reasons:"
    echo "   1. Authentication required (use GitHub Personal Access Token)"
    echo "   2. Repository doesn't exist or you don't have access"
    echo "   3. Network issues"
    echo ""
    echo "📋 To authenticate:"
    echo "   Option 1: Use Personal Access Token"
    echo "     git remote set-url origin https://YOUR_TOKEN@github.com/adarshvuppala-nu/kg_demo.git"
    echo ""
    echo "   Option 2: Use SSH (if you have SSH keys set up)"
    echo "     git remote set-url origin git@github.com:adarshvuppala-nu/kg_demo.git"
    echo ""
    echo "   Option 3: Use GitHub CLI"
    echo "     gh auth login"
    echo "     gh repo create adarshvuppala-nu/kg_demo --public --source=. --remote=origin --push"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
