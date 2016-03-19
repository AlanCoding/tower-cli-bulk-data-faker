# Create comprehensive fake data
python create_data.py all

# Create the POV users
python create_data.py pov

# Compute and display times for POV users
python time_test.py pov --detail --subviews > output.txt