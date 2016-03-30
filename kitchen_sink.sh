OUTPUT_FILE="output_$(python create_data.py version).txt"
echo "Saving data to the file:"
echo "${OUTPUT_FILE}"

# Create comprehensive fake data
echo ""
echo "creating bulk data"
python create_data.py runs/large_test.yml --silent > ${OUTPUT_FILE}

# Create the POV users
echo ""
echo "creating POV data"
python create_data.py pov runs/pov_users_large.yml --silent > ${OUTPUT_FILE}

# Compute and display times for POV users
echo ""
echo "running time test"
python time_test.py pov --detail --subviews > ${OUTPUT_FILE}