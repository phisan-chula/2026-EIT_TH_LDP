find OUTPUT_LDP -type f -name "*_OnePage.pdf" | sort | while read -r pdf; do
    echo "Opening: $pdf"
    evince "$pdf"
done
