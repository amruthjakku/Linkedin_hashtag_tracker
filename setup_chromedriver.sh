#!/bin/bash

# Install ChromeDriver using Homebrew
echo "Installing ChromeDriver..."
brew install --cask chromedriver

# Verify installation
chromedriver --version

# Grant permissions to ChromeDriver (required on macOS)
xattr -d com.apple.quarantine $(which chromedriver)

echo "ChromeDriver setup complete!"
