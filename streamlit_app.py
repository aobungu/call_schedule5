import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
import pandas as pd
import random
from datetime import datetime, timedelta
import streamlit as st

def generate_schedule(junior_residents, senior_residents, night_float, start_date, num_days, vacation_dict=None, specific_requests=None):
    if vacation_dict is None:
        vacation_dict = {}
    if specific_requests is None:
        specific_requests = {}
    
    schedule = []
    date = datetime.strptime(start_date, "%Y-%m-%d")
    junior_shift_counts = {r: 0 for r in junior_residents}
    senior_shift_counts = {r: 0 for r in senior_residents}
    last_assigned = {'junior_day': None, 'junior_night': None, 'senior': None}
    
    for _ in range(num_days):
        available_seniors = [r for r in senior_residents if r != last_assigned['senior'] and 
                              not any(start <= date <= end for start, end in vacation_dict.get(r, [])) and
                              date.strftime('%Y-%m-%d') not in vacation_dict.get(r, [])]
        
        if not available_seniors:
            raise ValueError(f"No available senior residents on {date.strftime('%Y-%m-%d')}")
        
        senior_resident = min(available_seniors, key=lambda r: senior_shift_counts[r])
        senior_shift_counts[senior_resident] += 1
        last_assigned['senior'] = senior_resident
        
        available_juniors = [r for r in junior_residents if r != night_float and r != last_assigned['junior_day'] and 
                              not any(start <= date <= end for start, end in vacation_dict.get(r, [])) and
                              date.strftime('%Y-%m-%d') not in vacation_dict.get(r, [])]
        
        if not available_juniors:
            raise ValueError(f"No available junior residents on {date.strftime('%Y-%m-%d')}")
        
        if date.weekday() == 5:  # Saturday - same junior for day and night
            junior_day = min(available_juniors, key=lambda r: junior_shift_counts[r])
            junior_night = junior_day
            junior_shift_counts[junior_day] += 2
        elif date.weekday() == 6:  # Sunday - night float starts
            junior_day = random.choice(available_juniors)
            junior_night = night_float
            junior_shift_counts[junior_day] += 1
        else:  # Monday-Friday - night float covers night, different junior for day
            junior_day = random.choice(available_juniors)
            junior_night = night_float
            junior_shift_counts[junior_day] += 1
        
        last_assigned['junior_day'] = junior_day
        last_assigned['junior_night'] = junior_night
        
        schedule.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Senior Resident': senior_resident,
            'Junior Resident (Day)': junior_day,
            'Junior Resident (Night)': junior_night
        })
        
        date += timedelta(days=1)
    
    return pd.DataFrame(schedule)

# Streamlit UI
st.title("Neurosurgery Call Schedule Generator")

junior_residents = st.text_area("Enter junior residents (comma-separated):").split(',')
senior_residents = st.text_area("Enter senior residents (comma-separated):").split(',')
night_float = st.selectbox("Select the night float junior resident:", junior_residents)
start_date = st.date_input("Select start date:").strftime('%Y-%m-%d')
num_days = st.number_input("Enter number of days:", min_value=1, max_value=365, value=30)

# Vacation input section
st.subheader("Enter vacation days or date ranges for residents")
vacation_dict = {}
for resident in junior_residents + senior_residents:
    st.write(f"**{resident}**")
    vacation_dates = st.text_area(f"Enter vacation dates for {resident} (comma-separated YYYY-MM-DD or ranges YYYY-MM-DD to YYYY-MM-DD):", key=resident)
    if vacation_dates:
        vacation_list = []
        for entry in vacation_dates.split(','):
            entry = entry.strip()
            if ' to ' in entry:
                start, end = entry.split(' to ')
                vacation_list.append((datetime.strptime(start.strip(), "%Y-%m-%d"), datetime.strptime(end.strip(), "%Y-%m-%d")))
            else:
                vacation_list.append(datetime.strptime(entry.strip(), "%Y-%m-%d"))
        vacation_dict[resident] = vacation_list

if st.button("Generate Schedule"):
    schedule_df = generate_schedule(junior_residents, senior_residents, night_float, start_date, num_days, vacation_dict)
    st.dataframe(schedule_df)
    
    csv = schedule_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Schedule as CSV", csv, "neurosurgery_schedule.csv", "text/csv")
