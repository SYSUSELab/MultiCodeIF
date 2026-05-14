#!/bin/bash

echo "=== Check the installation status of the programming language ==="

check_command() {
    if command -v $1 &> /dev/null; then
        echo "✓ $2: Installed"
        $1 $3 2>&1 | head -1
    else
        echo "✗ $2: Not installed"
    fi
    echo ""
}

check_command "python3" "Python" "--version"
check_command "node" "JavaScript (Node.js)" "--version"
check_command "java" "Java" "-version"
check_command "g++" "C++" "--version"
check_command "ghc" "Haskell" "--version"
check_command "swipl" "Prolog" "--version"
check_command "rustc" "Rust" "--version"
check_command "lua" "Lua" "-v"
check_command "julia" "Julia" "--version"
check_command "coffee" "CoffeeScript" "--version"
check_command "mcs" "C# (.NET)" "--version"
check_command "go" "Go" "version"
check_command "kotlinc" "Kotlin" "-version"
check_command "tsc" "TypeScript" "--version"
check_command "gcc" "C" "--version"