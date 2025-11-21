# 🚨 SECURITY ACTION REQUIRED

## Probleem
Het bestand `libris _ winkels.html` bevatte een Google Maps API key die is gecommit naar GitHub in de initial commit (423f381).

**API Key**: `AIzaSyA0VZVvLXNZPkx72uu77BxUJoMla6ttdxg`

**Status**:
- ✅ Bestand verwijderd uit huidige repository (commit 4f40bee)
- ❌ Nog steeds zichtbaar in git geschiedenis
- ❌ Publiek toegankelijk op GitHub

## STAP 1: Invalideer de API Key (DIRECT DOEN!)

1. Ga naar [Google Cloud Console](https://console.cloud.google.com/)
2. Navigeer naar: **APIs & Services** → **Credentials**
3. Zoek de key: `AIzaSyA0VZVvLXNZPkx72uu77BxUJoMla6ttdxg`
4. **Delete** of **Regenerate** de key
5. Maak een nieuwe key aan met **domain restrictions** (alleen jouw domeinen)

## STAP 2: Verwijder uit Git Geschiedenis (Optioneel maar aanbevolen)

**Waarschuwing**: Dit vereist een force push en zal de git geschiedenis herschrijven!

### Optie A: BFG Repo-Cleaner (Makkelijkst)

```bash
# Installeer BFG (macOS)
brew install bfg

# Backup maken
cd /Users/waltervandenberg/Code
cp -r BookCrawler BookCrawler-backup

# Verwijder bestand uit hele geschiedenis
cd BookCrawler
bfg --delete-files "libris _ winkels.html"
bfg --delete-files "libris.nl_winkels.png"

# Git garbage collection
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (DESTRUCTIEF!)
git push origin --force --all
```

### Optie B: Git Filter-Repo (Moderne methode)

```bash
# Installeer git-filter-repo
brew install git-filter-repo

# Backup maken
cd /Users/waltervandenberg/Code
cp -r BookCrawler BookCrawler-backup

# Verwijder specifieke bestanden
cd BookCrawler
git filter-repo --invert-paths --path "libris _ winkels.html" --path "libris.nl_winkels.png"

# Force push
git remote add origin https://github.com/vandenb/bookCrawler.git
git push origin --force --all
```

### Optie C: Nieuwe Repository (Veiligst)

Als je het zeker wilt weten:

```bash
# Verwijder .git directory
cd /Users/waltervandenberg/Code/BookCrawler
rm -rf .git

# Nieuwe git init (zonder oude geschiedenis)
git init
git add .
git commit -m "Clean repository without sensitive data"

# Push naar nieuwe branch of nieuwe repo
git remote add origin https://github.com/vandenb/bookCrawler.git
git push -u origin main --force
```

## STAP 3: Monitoring

Na het invalideren van de key, monitor je Google Cloud Console voor:
- Onverwacht API gebruik in de laatste 24 uur
- Requests van vreemde IP-adressen
- Quota overschrijdingen

## Preventie voor de Toekomst

1. **Pre-commit hooks**: Installeer tools zoals `git-secrets` of `gitleaks`
2. **Environment variables**: Gebruik `.env` files (in .gitignore)
3. **Secrets scanning**: Enable GitHub's secret scanning
4. **API restrictions**: Altijd domain/IP restrictions op API keys

## Links

- [Google Cloud Console](https://console.cloud.google.com/)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)

---

**Timestamp**: 2025-11-21
**Exposed Key**: AIzaSyA0VZVvLXNZPkx72uu77BxUJoMla6ttdxg
**First Commit**: 423f381 (Initial commit)
**Removed in**: 4f40bee (Cleanup commit)
