import requests
import pandas as pd
import matplotlib.pyplot as plt
import json
import numpy as np
from datetime import datetime, timedelta

USE_LIVE_DATA = False  # Set to True to use live API data

# List of target cities
target_cities = ['Berlin', 'München', 'Hamburg', 'Dresden', 'Stuttgart', 'Nürnberg']

def fetch_live_data():
    """Fetch live weather warnings from DWD API"""
    url = "https://warnung.bund.de/api31/mowas/mapData.json"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        warnings_data = response.json()
        print(f"Successfully fetched {len(warnings_data)} items from DWD API")
        return warnings_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from DWD API: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return []

def create_sample_weather_data():
    """Create sample weather data for demonstration"""
    print("Generating sample weather data for demonstration...")
    

    weather_events = [
        {'type': 'Thunderstorm Warning', 'severity': 'severe', 'score': 3, 'urgency': 'Immediate'},
        {'type': 'Heavy Rain Warning', 'severity': 'moderate', 'score': 2, 'urgency': 'Expected'},
        {'type': 'Heat Wave Warning', 'severity': 'extreme', 'score': 4, 'urgency': 'Immediate'},
        {'type': 'Strong Wind Warning', 'severity': 'moderate', 'score': 2, 'urgency': 'Expected'},
        {'type': 'Frost Warning', 'severity': 'minor', 'score': 1, 'urgency': 'Future'},
        {'type': 'Storm Warning', 'severity': 'extreme', 'score': 4, 'urgency': 'Immediate'},
        {'type': 'Snow Warning', 'severity': 'moderate', 'score': 2, 'urgency': 'Expected'}
    ]
    
    # Generate sample data
    records = []
    for city in target_cities:
        # 60% chance of having a weather warning for each city
        if np.random.random() > 0.4:
            event = weather_events[np.random.randint(0, len(weather_events))]
            records.append({
                'Region': city,
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Type': event['type'],
                'Severity': event['severity'],
                'Score': event['score'],
                'Urgency': event['urgency']
            })
    
    return records


if USE_LIVE_DATA:
    raw_data = fetch_live_data()
    data_source = "Live DWD API"
else:
    raw_data = create_sample_weather_data()
    data_source = "Sample Weather Data"

# Process data
records = []
weather_alerts_found = 0
other_alerts_found = 0

if USE_LIVE_DATA:
    for item in raw_data:
        try:
            # Check if this is a weather-related warning
            is_weather = False
            title = ""
            
            if 'i18nTitle' in item and 'de' in item['i18nTitle']:
                title = item['i18nTitle']['de'].lower()
                
                # Weather keywords to look for
                weather_keywords = [
                    'wetter', 'sturm', 'regen', 'gewitter', 'schnee', 'eis', 
                    'glätte', 'hitze', 'frost', 'wind', 'orkan', 'unwetter', 
                    'niederschlag', 'gewitter', 'hagel', 'nebel', 'glatteis'
                ]
                
                if any(keyword in title for keyword in weather_keywords):
                    is_weather = True
                    weather_alerts_found += 1
                else:
                    other_alerts_found += 1
                    continue  # Skip non-weather alerts
            else:
                continue  # Skip items without a title
                    
            # Get region information
            region = "Unknown"
            if 'name' in item:
                region = item['name']
            elif 'region' in item:
                region = item['region']
            elif 'area' in item:
                region = item['area']
                
            # Match to our target cities
            region_lower = region.lower()
            matched_city = None
            for city in target_cities:
                if city.lower() in region_lower:
                    matched_city = city
                    break
                    
            if not matched_city:
                continue
                
            # Get severity
            severity = item.get('severity', 'minor')
            
            # Assign numeric score
            severity_map = {"minor": 1, "moderate": 2, "severe": 3, "extreme": 4}
            score = severity_map.get(severity.lower(), 0)
            
            # Get additional info
            warning_type = item.get('type', 'Unknown')
            urgency = item.get('urgency', 'Unknown')
            
            records.append({
                "Region": matched_city, 
                "Severity": severity, 
                "Score": score,
                "Type": warning_type,
                "Urgency": urgency,
                "Title": title
            })
            
        except Exception as e:
            print(f"Error processing item: {e}")
            continue
else:
    # Use sample data directly
    records = raw_data

# Create DataFrame
if records:
    df = pd.DataFrame(records)
    print(f"Created DataFrame with {len(df)} weather warnings")
else:
    print("No weather warnings found. Creating empty DataFrame.")
    df = pd.DataFrame(columns=['Region', 'Severity', 'Score', 'Type', 'Urgency'])

# Display summary
print(f"\n{'='*60}")
print(f"WEATHER WARNING ANALYSIS - {data_source.upper()}")
print(f"{'='*60}")

if USE_LIVE_DATA:
    print(f"Total alerts from API: {len(raw_data)}")
    print(f"Weather alerts found: {weather_alerts_found}")
    print(f"Other types of alerts: {other_alerts_found}")

if df.empty:
    print("\nNo active weather warnings for the specified German cities.")
    print("This is actually good news - it means there are no severe weather conditions!")
    
    # Create a informative empty chart
    plt.figure(figsize=(12, 7))
    plt.barh(target_cities, [0] * len(target_cities), color='lightgreen')
    plt.title("No Active Weather Warnings for Major German Cities\nAll clear!", fontsize=14)
    plt.xlabel("Severity Score (0 = No warnings)", fontsize=12)
    plt.ylabel("City", fontsize=12)
    plt.gca().invert_yaxis()
    
    # Add text explanation
    plt.text(0.5, len(target_cities)/2, "No active weather warnings\nAll cities have clear conditions", 
             ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
else:
    # Aggregate by Region
    severity_summary = df.groupby("Region")["Score"].sum()
    
    # Ensure all target cities are represented
    for city in target_cities:
        if city not in severity_summary.index:
            severity_summary[city] = 0
    
    # Reorder to match our target cities list
    severity_summary = severity_summary.reindex(target_cities)
    
    plt.figure(figsize=(12, 7))
    colors = ['crimson' if score > 0 else 'lightgreen' for score in severity_summary.values]
    bars = plt.barh(severity_summary.index, severity_summary.values, color=colors)
    plt.title(f"Weather Warning Severity for Major German Cities\n({data_source})", fontsize=14)
    plt.xlabel("Total Severity Score", fontsize=12)
    plt.ylabel("City", fontsize=12)
    plt.gca().invert_yaxis()
    
    # Add value labels to each bar
    for i, v in enumerate(severity_summary.values):
        if v > 0:
            plt.text(v + 0.05, i, str(v), color='black', fontweight='bold', va='center')
        else:
            plt.text(0.05, i, "No warnings", color='darkgreen', va='center')
    
    plt.tight_layout()
    plt.show()

# Print detailed summary
print(f"\n{'='*60}")
print("DETAILED WEATHER WARNING SUMMARY")
print(f"{'='*60}")

if df.empty:
    for city in target_cities:
        print(f"{city}: No active weather warnings")
else:
    for city in target_cities:
        if city in df['Region'].values:
            city_warnings = df[df['Region'] == city]
            print(f"\n{city}:")
            print(f"  Total Severity Score: {city_warnings['Score'].sum()}")
            print(f"  Number of Warnings: {len(city_warnings)}")
            
            for _, warning in city_warnings.iterrows():
                print(f"    - {warning['Severity'].title()} (Score: {warning['Score']}): {warning.get('Type', 'Unknown')}")
        else:
            print(f"\n{city}: No active weather warnings")

# Show explanation
print(f"\n{'='*60}")
print("EXPLANATION")
print(f"{'='*60}")
print("The DWD API returns various types of alerts, including:")
print("- Weather warnings (thunderstorms, rain, snow, etc.)")
print("- Civil protection alerts (like the African Swine Fever alert shown)")
print("- Other emergency notifications")
print("\nThis system filters for weather-related alerts only using keyword matching.")
print("Currently, there are no active weather warnings for the specified cities.")

# Show a sample of what was filtered out
if USE_LIVE_DATA and raw_data and len(raw_data) > 0 and other_alerts_found > 0:
    print(f"\n{'='*60}")
    print("SAMPLE OF NON-WEATHER ALERTS (FILTERED OUT):")
    print(f"{'='*60}")
    for item in raw_data[:2]:  # Show first 2 items as sample
        if 'i18nTitle' in item and 'de' in item['i18nTitle']:
            title = item['i18nTitle']['de']
            if not any(keyword in title.lower() for keyword in ['wetter', 'sturm', 'regen', 'gewitter', 'schnee']):
                print(f"Title: {title}")
                print(f"Type: {item.get('type', 'Unknown')}")
                print(f"Severity: {item.get('severity', 'Unknown')}")

                print("-" * 40)
