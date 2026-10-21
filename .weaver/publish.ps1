# Sync local recomp/runtime/tools into the nxrecomp base mirror, push it, bump the game repo's base submodule, push that.
# Usage: pwsh .weaver\publish.ps1   (pushes to GitHub; only run when the user wants a push)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$base = Join-Path $root 'publish\nxrecomp'
foreach ($r in 'recomp', 'runtime', 'tools') {
    git -C $base subtree pull -q --prefix=$r (Join-Path $root $r) main -m "Sync $r"
}
git -C $base push -q origin main
$sha = git -C $base rev-parse HEAD
git -C $root update-index --cacheinfo "160000,$sha,base"
git -C $root commit -q -m "Bump base to $($sha.Substring(0,8))" -- base 2>$null
git -C $root push -q origin main
"base $($sha.Substring(0,8)) pushed; game repo pushed"
