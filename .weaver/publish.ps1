# Publish both GitHub repos.
#  1. Sync local recomp/runtime/tools (main) into the base mirror publish\nxrecomp and push it (github.com/drakolordx7/nxrecomp).
#  2. Build the game repo for GitHub from the local root repo with local tooling files (CLAUDE.md, .claude/, docs/BRIEF_PREAMBLE.md)
#     removed from all history (git filter-repo, deterministic), bump its base submodule, and push it
#     (github.com/drakolordx7/MetroidPrimeRemasteredRecomp).
# Usage: pwsh .weaver\publish.ps1 [-Force]   (-Force only for the one-time switch to the scrubbed history; the user approved it)
param([switch]$Force)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$base = Join-Path $root 'publish\nxrecomp'
foreach ($r in 'recomp', 'runtime', 'tools') {
    git -C $base subtree pull -q --prefix=$r (Join-Path $root $r) main -m "Sync $r"
}
git -C $base push -q origin main
$sha = git -C $base rev-parse HEAD

# the game repo: bump base locally first (commit from the index; a pathspec commit reads the uninitialised submodule folder)
git -C $root update-index --cacheinfo "160000,$sha,base"
$staged = @(git -C $root diff --cached --name-only)
if ($staged.Count -eq 1 -and $staged[0] -eq 'base') {
    git -C $root commit -q -m "Bump base to $($sha.Substring(0,8))"
} elseif ($staged.Count -gt 0) {
    throw "game repo has other staged changes ($($staged -join ', ')); commit them first"
}

$scrub = Join-Path $root 'publish\game-scrub'
if (Test-Path $scrub) { Remove-Item $scrub -Recurse -Force }
git clone -q --no-local $root $scrub
git -C $scrub filter-repo --force --invert-paths --path CLAUDE.md --path .claude/ --path docs/BRIEF_PREAMBLE.md
$left = @(git -C $scrub log --all --name-only --format= | Select-String -Pattern '(^|/)(CLAUDE\.md|\.claude/|BRIEF_PREAMBLE)')
if ($left.Count) { throw "scrub left tooling files in history" }
git -C $scrub remote add origin https://github.com/drakolordx7/MetroidPrimeRemasteredRecomp.git
if ($Force) { git -C $scrub push -q --force origin main } else { git -C $scrub push -q origin main }
"base $($sha.Substring(0,8)) pushed; game repo (scrubbed history, $(git -C $scrub rev-parse --short HEAD)) pushed"
