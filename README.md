# Tetra Energies – website and staff portal

Source for the Tetra Energies public website and the staff portal. Every change is kept in the history of this
repository, so any earlier version can be seen or restored.

| Folder | Published to | Cloudflare Pages project |
|---|---|---|
| `website/` | https://www.tetraenergies.com (English) and `/es/` (Spanish) | `tetraenergies-web` |
| `portal/` | https://portal.tetraenergies.net (email-code login, approved users only) | `tetraenergies-portal` |

Both are plain static files (HTML, images, SVG maps); there is no build step.

## Publishing

A change to `website/` or `portal/` on the `main` branch is published automatically by the workflows in
`.github/workflows/` (usually within a minute). Progress shows under the repository's **Actions** tab. A workflow can
also be run by hand from that tab ("Run workflow").

The workflows need one repository secret, `CLOUDFLARE_API_TOKEN`: a Cloudflare API token with
**Account › Cloudflare Pages › Edit** permission for the Tetra Cloudflare account.

Fallback: zip the folder and upload it in the Cloudflare dashboard (Workers & Pages › project › Create deployment).

## Notes

* **Public website shows only publicly known information.** Do not add CPR volumes, investment amounts, investor
  terms, well locations (other than the published discovery markers), or other team members or advisers.
* **English and Spanish pages must be kept in step.** `website/index.html` and `website/es/index.html` share the same
  layout; the Spanish page uses `../` paths for images and `maps/es/` for the Spanish maps.
* **Maps** (`website/maps/*.svg`, Spanish in `website/maps/es/`) are generated, not hand-edited. The master copies and
  the generator live on the corporate drive at `T:\PROJECTS\Global\GIS_database\GIS_export_maps\external webmaps\`
  (see its README). Regenerate there and copy the SVGs here.
* DNS: `www.tetraenergies.com` is a CNAME at GoDaddy to `tetraenergies-web.pages.dev`; the bare domain forwards to
  `https://www.tetraenergies.com`. Email for `tetraenergies.com` (Microsoft 365) stays at GoDaddy and is not affected
  by anything here. `tetraenergies.net` is on Cloudflare and carries the portal and the Tetra toolkit (toolkit.tetraenergies.net: Volumetrics and Portfolio model; the old volumetrics.tetraenergies.net redirects there).
* The Tetra toolkit itself (Volumetrics and Portfolio model) is in the separate repository `mobiusadvisory/tetra-volumetrics`; the server updates itself from its `main` branch.
* UK English throughout the English page; Peruvian Spanish (es-PE) on the Spanish page.
