# GitHub Pages & Custom Domain Deployment Guide

This guide walks you through deploying the documentation to GitHub Pages and configuring a custom subdomain with GoDaddy.

## Step A: Deploy to GitHub Pages

### 1. Enable GitHub Pages

1. **Go to repository settings**:
   - Navigate to `https://github.com/yourusername/sweagent/settings`
   - Click "Pages" in the left sidebar

2. **Configure source**:
   - Under "Source", select "GitHub Actions"
   - This uses the workflow in `.github/workflows/deploy-docs.yml`

3. **Verify workflow**:
   - Check "Actions" tab for deployment status
   - Initial deployment takes 2-5 minutes

### 2. Test Initial Deployment

- Docs will be available at: `https://yourusername.github.io/sweagent`
- Built from `/docs` directory using Jekyll
- Auto-deploys on pushes to `main` branch

## Step B: Custom Domain Setup (GoDaddy + GitHub Pages)

### 1. Configure GitHub Pages Custom Domain

1. **Set custom domain**:
   - Go to Settings → Pages
   - Under "Custom domain", enter: `docs.yourdomain.com`
   - Click "Save"

2. **Verify CNAME file**:
   - GitHub creates `/docs/CNAME` with your domain
   - File should contain: `docs.yourdomain.com`

### 2. Configure GoDaddy DNS

1. **Access GoDaddy DNS**:
   - Log into GoDaddy account
   - Go to "My Products" → "DNS"
   - Click "Manage" for your domain

2. **Add CNAME record**:
   ```
   Type: CNAME
   Name: docs
   Value: yourusername.github.io
   TTL: 600 seconds
   ```

3. **Save changes**:
   - DNS propagation: 10 minutes to 24 hours

### 3. Enable HTTPS

1. **Wait for DNS propagation** (10-60 minutes)
2. **Return to GitHub Pages settings**
3. **Check "Enforce HTTPS"** when available

## Verification

### Check GitHub Pages
```bash
curl -I https://yourusername.github.io/sweagent
# Should return 200 OK
```

### Verify DNS
```bash
nslookup docs.yourdomain.com
# Should resolve to yourusername.github.io
```

### Test Custom Domain
- Visit: `https://docs.yourdomain.com`
- Navigate through pages
- Verify all links work

## Troubleshooting

### Common Issues

**Page build failed**:
- Check Actions tab for errors
- Verify `_config.yml` syntax
- Ensure markdown files are valid

**Custom domain not working**:
- Verify CNAME record: `docs` → `yourusername.github.io`
- Wait for DNS propagation (up to 24 hours)
- Check CNAME file exists in `/docs`

**SSL certificate issues**:
- Wait for DNS propagation
- GitHub needs time to provision SSL
- Try toggling "Enforce HTTPS"

### DNS Troubleshooting

```bash
# Check DNS status
dig docs.yourdomain.com CNAME

# Test different DNS servers
dig @8.8.8.8 docs.yourdomain.com CNAME
dig @1.1.1.1 docs.yourdomain.com CNAME
```

## Configuration Files Created

### `.github/workflows/deploy-docs.yml`
- Automated Jekyll build and deployment
- Triggers on pushes to main branch
- Uses GitHub's official Actions

### `docs/_config.yml`
- Jekyll configuration
- Site metadata and theme settings
- Navigation structure

### `docs/CNAME`
- Contains: `docs.yourdomain.com`
- Required for custom domain

## Updating Documentation

### Automatic Updates
- Push changes to `main` branch
- GitHub Actions builds and deploys
- Changes appear within 2-5 minutes

### Manual Deployment
- Go to Actions → "Deploy Documentation"
- Click "Run workflow"

## Final Configuration Steps

1. **Update repository URLs** in documentation files
2. **Replace placeholder domain** with actual domain
3. **Test all functionality** end-to-end
4. **Set up monitoring** if needed

Your documentation will be live at: `https://docs.yourdomain.com` 🎉

## Next Steps After Deployment

1. Update any hardcoded URLs in the documentation
2. Test all navigation and links
3. Set up any additional monitoring or analytics
4. Consider setting up a redirect from the main domain if needed