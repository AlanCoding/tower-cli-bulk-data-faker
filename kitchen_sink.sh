# Create comprehensive fake data
python create_data.py runs/large_test.yml

# Create the POV users
python create_data.py pov runs/pov_users_large.yml

# Compute and display times for POV users
python time_test.py pov --detail --subviews > output.txt