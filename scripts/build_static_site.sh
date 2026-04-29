#!/usr/bin/env bash
set -euo pipefail

rm -rf public
mkdir -p public

cp ias_srfp2026_dashboard.html public/index.html
cp ias_srfp2026_selected_people.csv public/
cp ias_srfp2026_subject_results.csv public/
cp ias_srfp2026_route_summary.md public/
