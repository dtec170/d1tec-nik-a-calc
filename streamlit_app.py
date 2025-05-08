import streamlit as st
import matplotlib.pyplot as plt
import time

# Import the calculation functions from the original file
def calculate_effective_ammo_with_bastion(base_ammo):
    """
    Calculate effective ammo when using Bastion Cube (refunds 4 ammo every 10th shot)
    """
    shots_fired = 0
    actual_shots = 0
    
    # Keep firing until we've used up all ammo
    while actual_shots < base_ammo:
        shots_fired += 1
        actual_shots += 1
        
        # Every 10th shot refunds 4 ammo
        if shots_fired % 10 == 0:
            actual_shots -= 4  # Refund 4 ammo
            
    return shots_fired

def calculate_uptime(total_ammo, fire_rate, reload_time, is_mg=False, 
                     bastion_cube=False, resilience=0, ammo_bonus=0):
    """
    Calculate the weapon uptime based on the given parameters.
    """
    cover_time = 0.23333  # Cover time during reload in seconds
    
    # Apply ammo bonus
    if ammo_bonus > 0:
        effective_total_ammo = int(total_ammo * (1 + ammo_bonus / 100))
    else:
        effective_total_ammo = total_ammo
    
    # Apply resilience to reload time (only if Bastion Cube is not active)
    if resilience > 0 and not bastion_cube:
        effective_reload_time = reload_time * (1 - resilience / 100)
    else:
        effective_reload_time = reload_time
    
    # Calculate effective shots with Bastion Cube (only if Resilience is not active)
    if bastion_cube:
        effective_shots = calculate_effective_ammo_with_bastion(effective_total_ammo)
    else:
        effective_shots = effective_total_ammo
    
    # Machine gun wind-up calculation
    if is_mg:
        wind_up_time = 2.55  # Wind up time in seconds
        wind_up_ammo = 47  # Ammo used during wind up
        
        # Calculate shooting time
        if effective_shots <= wind_up_ammo:
            shooting_time = (effective_shots / wind_up_ammo) * wind_up_time
        else:
            remaining_shots = effective_shots - wind_up_ammo
            remaining_time = remaining_shots / fire_rate
            shooting_time = wind_up_time + remaining_time
    else:
        # Normal weapon calculation
        shooting_time = effective_shots / fire_rate
        wind_up_time = 0
    
    # Calculate total magazine cycle time
    total_time = effective_reload_time + shooting_time + cover_time
    
    # Calculate uptime
    uptime = (shooting_time / total_time) * 100
    
    return {
        'uptime': uptime,
        'shooting_time': shooting_time,
        'total_time': total_time,
        'reload_time': effective_reload_time,
        'cover_time': cover_time,
        'effective_ammo': effective_shots,
        'base_ammo': total_ammo
    }

def simulate_ammo_consumption(total_ammo, fire_rate, reload_time, is_mg=False, 
                              bastion_cube=False, resilience=0, ammo_bonus=0, 
                              simulation_time=30):
    """
    Simulates ammo consumption over time.
    """
    cover_time = 0.23333  # Cover time during reload
    
    # Apply ammo bonus
    if ammo_bonus > 0:
        max_ammo = int(total_ammo * (1 + ammo_bonus / 100))
    else:
        max_ammo = total_ammo
        
    # Apply resilience to reload time
    if resilience > 0:
        effective_reload_time = reload_time * (1 - resilience / 100)
    else:
        effective_reload_time = reload_time
        
    # Set up tracking arrays
    time_points = [0]
    ammo_points = [max_ammo]
    
    current_time = 0
    current_ammo = max_ammo
    shots_fired = 0  # Total shots fired across all magazines
    shots_in_mag = 0  # Shots fired in current magazine (for Bastion Cube tracking)
    total_shots_fired = 0  # Track total shots for return value
    
    # We need to track actual firing time vs. reload time
    total_reload_time = 0  # Total time spent reloading
    is_reloading = False   # Track if we're currently reloading
    
    # MG parameters
    wind_up_time = 2.55 if is_mg else 0
    wind_up_ammo = 47 if is_mg else 0
    
    # Start with wind-up period for MG
    if is_mg and current_ammo > 0:
        # Calculate how long the wind-up will take based on available ammo
        wind_up_duration = min(wind_up_time, (current_ammo / wind_up_ammo) * wind_up_time)
        # Calculate ammo used during wind-up
        ammo_used_during_windup = min(current_ammo, wind_up_ammo)
        
        current_time += wind_up_duration
        current_ammo -= ammo_used_during_windup
        total_shots_fired += ammo_used_during_windup
        shots_fired += ammo_used_during_windup
        shots_in_mag += ammo_used_during_windup
        
        time_points.append(current_time)
        ammo_points.append(current_ammo)
    
    # Continue simulating until we reach the simulation time
    while current_time < simulation_time:
        # If we're out of ammo, reload
        if current_ammo <= 0:
            # Start reload process
            is_reloading = True
            reload_start_time = current_time
            
            # Reload and cover time
            reload_duration = effective_reload_time + cover_time
            current_time += reload_duration
            total_reload_time += reload_duration
            current_ammo = max_ammo
            shots_in_mag = 0  # Reset only shots in current magazine
            
            # Finished reloading
            is_reloading = False
            
            time_points.append(current_time)
            ammo_points.append(current_ammo)
            continue
        
        # Calculate time to fire one shot
        if is_mg and current_ammo == max_ammo:
            # We're starting a fresh magazine for an MG, so we need wind-up again
            if current_ammo <= wind_up_ammo:
                time_to_fire = (1 / wind_up_ammo) * wind_up_time
            else:
                # Skip to after wind-up
                time_to_fire = 1 / fire_rate
                current_time += wind_up_time
                current_ammo -= wind_up_ammo
                total_shots_fired += wind_up_ammo
                shots_fired += wind_up_ammo
                shots_in_mag += wind_up_ammo
                
                # Record the state after wind-up
                time_points.append(current_time)
                ammo_points.append(current_ammo)
                continue
        else:
            time_to_fire = 1 / fire_rate
        
        # Fire one shot
        current_time += time_to_fire
        current_ammo -= 1
        shots_fired += 1
        shots_in_mag += 1
        total_shots_fired += 1
        
        # Apply Bastion Cube effect - use total shots for 10th shot calculation
        if bastion_cube and shots_fired % 10 == 0:
            current_ammo = min(current_ammo + 4, max_ammo)  # Refund 4 ammo, don't exceed max
        
        # Record point only when we cross whole number boundaries or at end of ammo
        if int(time_points[-1]) != int(current_time) or current_ammo <= 0:
            time_points.append(current_time)
            ammo_points.append(current_ammo)
    
    # Calculate uptime as percentage of total simulation time
    total_shooting_time = simulation_time - total_reload_time
    return time_points, ammo_points, total_shots_fired, total_shooting_time

# Add custom CSS for light theme
def add_custom_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom, #f0f2f5, #e8ecf1, #dfe6e9);
        color: #2d3436;
    }
    .css-1lcbmhc, .css-1wrcr25, .css-ocqkz7 {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    .stButton>button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stop-button > button {
        background-color: #e74c3c !important;
    }
    .stop-button > button:hover {
        background-color: #c0392b !important;
    }
    h1, h2, h3 {
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .results-container {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        color: #2d3436;
    }
    a {
        color: #2980b9;
    }
    .stDataFrame {
        color: #2d3436;
    }
    </style>
    """, unsafe_allow_html=True)

# Remove GIF-related functions and modify animation to be time-based
def create_animation(total_ammo, fire_rate, reload_time, is_mg=False, 
                    bastion_cube=False, resilience=0, ammo_bonus=0,
                    speed_factor=1.0):
    
    # Apply ammo bonus
    if ammo_bonus > 0:
        max_ammo = int(total_ammo * (1 + ammo_bonus / 100))
    else:
        max_ammo = total_ammo
        
    # Apply resilience to reload time
    if resilience > 0:
        effective_reload_time = reload_time * (1 - resilience / 100)
    else:
        effective_reload_time = reload_time
    
    # Add cover time to reload
    effective_reload_time += 0.23333  # Cover time
    
    # Setup placeholders for the UI elements
    chart_placeholder = st.empty()
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    metrics_placeholder = st.empty()
    debug_placeholder = st.empty()  # For debugging info if needed
    
    # Initialize variables
    current_ammo = max_ammo
    is_reloading = False
    is_winding_up = is_mg
    reload_start_time = 0
    simulation_time = 0
    time_points = [0]
    ammo_points = [max_ammo]
    total_shots = 0
    fractional_shots = 0  # Track partial shots
    
    # Machine gun parameters
    wind_up_time = 2.55 if is_mg else 0
    wind_up_ammo = 47 if is_mg else 0
    windup_progress_shots = 0
    
    # Setup real-time tracking
    start_time = time.time()
    last_update_time = start_time
    frame_count = 0
    
    # Initialize stop flag in session state if it doesn't exist
    if 'stop_animation' not in st.session_state:
        st.session_state.stop_animation = False
    
    try:
        while not st.session_state.stop_animation:
            current_time = time.time()
            frame_count += 1
            
            # Calculate real elapsed time since last update
            elapsed_since_last = current_time - last_update_time
            last_update_time = current_time
            
            # Scale elapsed time by speed factor to get simulation time increment
            sim_time_increment = elapsed_since_last * speed_factor
            
            # Update simulation time
            simulation_time += sim_time_increment
            
            # Handle reloading
            if is_reloading:
                elapsed_reload_time = simulation_time - reload_start_time
                reload_progress = elapsed_reload_time / effective_reload_time
                
                if reload_progress < 1.0:
                    # Still reloading
                    status_placeholder.markdown(f"### 🔄 RELOADING...")
                    progress_placeholder.progress(min(1.0, reload_progress))
                else:
                    # Finished reloading
                    current_ammo = max_ammo
                    is_reloading = False
                    is_winding_up = is_mg
                    windup_progress_shots = 0
                    progress_placeholder.empty()
            
            # Start reload if ammo is empty
            elif current_ammo <= 0:
                is_reloading = True
                reload_start_time = simulation_time
                status_placeholder.markdown(f"### 🔄 STARTING RELOAD...")
                progress_placeholder.progress(0.0)
            
            # Handle firing (only when not reloading)
            elif not is_reloading:
                # Handle MG wind-up
                if is_winding_up:
                    status_placeholder.markdown(f"### 🔄 WINDING UP...")
                    
                    # Calculate ammo used during wind-up based on real time
                    windup_rate = wind_up_ammo / wind_up_time  # ammo per second during windup
                    ammo_used_this_frame = windup_rate * sim_time_increment
                    
                    # Update windup progress shots
                    windup_progress_shots += ammo_used_this_frame
                    
                    # Show windup progress
                    progress_percentage = min(1.0, windup_progress_shots / wind_up_ammo)
                    progress_placeholder.progress(progress_percentage)
                    
                    # Reduce ammo
                    whole_shots = int(ammo_used_this_frame)
                    fractional_shots += ammo_used_this_frame - whole_shots
                    
                    # Handle accumulated fractional shots
                    if fractional_shots >= 1:
                        extra_shots = int(fractional_shots)
                        whole_shots += extra_shots
                        fractional_shots -= extra_shots
                    
                    if whole_shots > 0:
                        # Limit shots to available ammo
                        actual_shots = min(whole_shots, current_ammo)
                        # Update ammo and shots
                        current_ammo = max(0, current_ammo - actual_shots)
                        total_shots += actual_shots
                        
                        # Adjust fractional shots if we couldn't fire all shots
                        if actual_shots < whole_shots:
                            # We hit empty - don't carry over fractional shots
                            fractional_shots = 0
                    
                    # Check if wind-up complete
                    if windup_progress_shots >= wind_up_ammo:
                        is_winding_up = False
                        progress_placeholder.empty()
                
                # Normal firing (or MG after wind-up)
                else:
                    status_placeholder.markdown(f"### 🔥 FIRING...")
                    
                    # Calculate shots fired in this time increment
                    shots_this_frame = fire_rate * sim_time_increment
                    
                    # Add to fractional tracking and calculate whole shots
                    fractional_shots += shots_this_frame
                    whole_shots = int(fractional_shots)
                    fractional_shots -= whole_shots
                    
                    # Update ammo and total shots
                    if whole_shots > 0:
                        # Limit shots to available ammo
                        actual_shots = min(whole_shots, current_ammo)
                        current_ammo = max(0, current_ammo - actual_shots)
                        total_shots += actual_shots
                        
                        # Reset fractional shots if we're out of ammo
                        if actual_shots < whole_shots:
                            fractional_shots = 0
                        
                        # Apply Bastion Cube effect
                        if bastion_cube and actual_shots > 0:
                            # Check each shot that was fired for 10th shot
                            bastion_refunds = 0
                            for i in range(actual_shots):
                                shot_number = total_shots - actual_shots + i + 1
                                if shot_number % 10 == 0:
                                    bastion_refunds += 4
                            
                            if bastion_refunds > 0:
                                current_ammo = min(current_ammo + bastion_refunds, max_ammo)
                                status_placeholder.markdown(f"### 🔄 BASTION CUBE +{bastion_refunds} AMMO")
            
            # Update time and ammo points for the chart (manage length for performance)
            time_points.append(simulation_time)
            ammo_points.append(current_ammo)
            
            # Keep chart efficient by limiting points when simulation gets long
            if len(time_points) > 200:
                # Retain more recent history
                step = max(1, len(time_points) // 200)
                time_points = time_points[::step]
                ammo_points = ammo_points[::step]
                time_points.append(simulation_time)  # Always keep the latest point
                ammo_points.append(current_ammo)
            
            # Update metrics
            col1, col2, col3 = metrics_placeholder.columns(3)
            col1.metric("Time", f"{simulation_time:.2f}s")
            col2.metric("Shots Fired", f"{total_shots}")
            col3.metric("Ammo", f"{current_ammo}/{max_ammo}")
            
            # Create and update the chart
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(time_points, ammo_points, '-', color='blue', linewidth=2)
            ax.set_title(f'Real-Time Ammo Consumption', fontsize=12)
            ax.set_xlabel('Time (seconds)')
            ax.set_ylabel('Ammo Remaining')
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.set_ylim(0, max_ammo * 1.1)  # Give some headroom
            chart_placeholder.pyplot(fig)
            plt.close(fig)
            
            # Control frame rate to prevent UI freezing
            # Use a very short sleep for more responsive updates
            time.sleep(0.001)
            
    except st.runtime.scriptrunner.StopException:
        st.warning("Animation stopped by system")
        return
    finally:
        # Just stop the animation without cleaning up or resetting
        # This preserves the last frame of the animation
        if st.session_state.stop_animation:
            status_placeholder.markdown(f"### ⏹️ ANIMATION PAUSED")
        # Don't reset the stop flag or empty any placeholders

# App main function
def main():
    add_custom_css()
    
    st.title("NIKKE Weapon Uptime Calculator")
    st.markdown("### Calculate and visualize weapon performance")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["💼 Calculator", "📊 Ammo Consumption", "🎬 Animated Simulation"])
    
    with tab1:
        st.header("Weapon Uptime Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            total_ammo = st.number_input("Base Ammo", min_value=1, value=300, step=1)
            fire_rate = st.number_input("Fire Rate (shots/sec)", min_value=0.1, value=60.0, step=0.1)
            reload_time = st.number_input("Reload Time (sec)", min_value=0.1, value=2.3, step=0.1)
            st.markdown("###### Weapon Type")
            is_mg = st.checkbox("Machine Gun (MG)")
            
        with col2:
            equipment = st.radio(
                "Equipment",
                ["None", "Bastion Cube", "Resilience"]
            )
            ammo_bonus = st.number_input("Max Ammo Bonus (%)", min_value=0, value=0, step=1)
            
        # Set values based on equipment selection
        bastion_cube = equipment == "Bastion Cube"
        resilience = 29.69 if equipment == "Resilience" else 0
        
        if st.button("Calculate Uptime", key="calc_button"):
            # Calculate uptime
            results = calculate_uptime(total_ammo, fire_rate, reload_time, is_mg, 
                                     bastion_cube, resilience, ammo_bonus)
            
            # Display results
            st.markdown("### Results")
            
            # Display results first (removed column layout)
            st.markdown(f"""
            <div class="results-container">
            <h3>Uptime: <span style="color:#2ecc71">{results['uptime']:.2f}%</span></h3>
            <p>Effective Ammo: {results['effective_ammo']} (Base: {results['base_ammo']})</p>
            <p>Shooting Time: {results['shooting_time']:.2f}s</p>
            <p>Total Magazine Cycle: {results['total_time']:.2f}s</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display breakdown below results
            st.subheader("Calculation Breakdown")
            breakdown = f""
            if ammo_bonus > 0:
                breakdown += f"- Base ammo: {total_ammo} + {ammo_bonus}% bonus = {results['base_ammo']} ammo\n"
            else:
                breakdown += f"- Base ammo: {total_ammo}\n"
                
            if bastion_cube:
                breakdown += f"- Bastion Cube: Active (refunds 4 ammo every 10th shot)\n"
                breakdown += f"- Effective shots: {results['effective_ammo']}\n"
                
            if resilience > 0:
                breakdown += f"- Reload time: {reload_time}s - {resilience}% = {results['reload_time']:.2f}s\n"
            else:
                breakdown += f"- Reload time: {reload_time}s\n"
                
            if is_mg:
                breakdown += f"- Machine Gun with wind-up time: 2.55s for first 47 ammo\n"
                if results['effective_ammo'] <= 47:
                    breakdown += f"- Shooting time: ({results['effective_ammo']}/47) * 2.55 = {results['shooting_time']:.2f}s\n"
                else:
                    remaining_ammo = results['effective_ammo'] - 47
                    remaining_time = remaining_ammo / fire_rate
                    breakdown += f"- Shooting time: 2.55s + ({remaining_ammo}/{fire_rate}) = {results['shooting_time']:.2f}s\n"
            else:
                breakdown += f"- Shooting time: {results['effective_ammo']}/{fire_rate} = {results['shooting_time']:.2f}s\n"
                
            breakdown += f"- Magazine cycle: {results['shooting_time']:.2f}s + {results['reload_time']:.2f}s (reload) + {results['cover_time']:.2f}s (cover) = {results['total_time']:.2f}s\n"
            breakdown += f"- Uptime: {results['shooting_time']:.2f}s / {results['total_time']:.2f}s = {results['uptime']:.2f}%"
            
            st.text_area("", breakdown, height=300, key="breakdown")
            
    with tab2:
        st.header("Ammo Consumption Visualization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            ammo_cons_total_ammo = st.number_input("Base Ammo", min_value=1, value=300, step=1, key="vis_ammo")
            ammo_cons_fire_rate = st.number_input("Fire Rate (shots/sec)", min_value=0.1, value=60.0, step=0.1, key="vis_fire")
            ammo_cons_reload_time = st.number_input("Reload Time (sec)", min_value=0.1, value=2.3, step=0.1, key="vis_reload")
            st.markdown("###### Weapon Type")
            ammo_cons_is_mg = st.checkbox("Machine Gun (MG)", key="vis_mg")
        
        with col2:
            ammo_cons_sim_time = st.number_input("Simulation Time (sec)", min_value=1, value=30, step=1)
            ammo_cons_ammo_bonus = st.number_input("Max Ammo Bonus (%)", min_value=0, value=0, step=1, key="vis_bonus")
        
        ammo_cons_equipment = st.radio(
            "show equipment comparison",
            ["Compare Both", "Bastion Cube Only", "Resilience Only"],
            key="vis_equip"
        )
        
        if st.button("Generate Ammo Consumption Graph", key="gen_button"):
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.tight_layout(pad=5)
            
            # Fixed values for comparison
            resilience_value = 29.69  # Resilience value per requirements
            
            # Always show baseline
            baseline_times, baseline_ammo, baseline_shots, baseline_shoot_time = simulate_ammo_consumption(
                ammo_cons_total_ammo, ammo_cons_fire_rate, ammo_cons_reload_time, ammo_cons_is_mg, 
                bastion_cube=False, resilience=0, ammo_bonus=ammo_cons_ammo_bonus,
                simulation_time=ammo_cons_sim_time
            )
            ax.plot(baseline_times, baseline_ammo, '-', color='gray', alpha=0.7, label='No Equipment')
            
            # Add Bastion Cube line if requested
            if ammo_cons_equipment in ["Compare Both", "Bastion Cube Only"]:
                bastion_times, bastion_ammo, bastion_shots, bastion_shoot_time = simulate_ammo_consumption(
                    ammo_cons_total_ammo, ammo_cons_fire_rate, ammo_cons_reload_time, ammo_cons_is_mg, 
                    bastion_cube=True, resilience=0, ammo_bonus=ammo_cons_ammo_bonus,
                    simulation_time=ammo_cons_sim_time
                )
                ax.plot(bastion_times, bastion_ammo, '-', color='green', label='Bastion Cube')
            
            # Add Resilience line if requested
            if ammo_cons_equipment in ["Compare Both", "Resilience Only"]:
                resilience_times, resilience_ammo, resilience_shots, resilience_shoot_time = simulate_ammo_consumption(
                    ammo_cons_total_ammo, ammo_cons_fire_rate, ammo_cons_reload_time, ammo_cons_is_mg, 
                    bastion_cube=False, resilience=resilience_value, ammo_bonus=ammo_cons_ammo_bonus,
                    simulation_time=ammo_cons_sim_time
                )
                ax.plot(resilience_times, resilience_ammo, '-', color='blue', label='Resilience')
            
            # Create info text
            info_text = f"Simulation Results ({ammo_cons_sim_time}s):\n"
            info_text += f"No Equipment: {baseline_shots} shots\n"
            
            if ammo_cons_equipment in ["Compare Both", "Bastion Cube Only"]:
                info_text += f"Bastion Cube: {bastion_shots} shots\n"
            
            if ammo_cons_equipment in ["Compare Both", "Resilience Only"]:
                info_text += f"Resilience: {resilience_shots} shots"
            
            # Improve title and layout
            title = f'Ammo Consumption Over Time ({ammo_cons_sim_time}s)'
            subtitle = f'Base Ammo: {ammo_cons_total_ammo}, Fire Rate: {ammo_cons_fire_rate}/s, Reload: {ammo_cons_reload_time}s'
            
            if ammo_cons_is_mg:
                subtitle += ", Machine Gun"
            if ammo_cons_ammo_bonus > 0:
                subtitle += f", +{ammo_cons_ammo_bonus}% Ammo"
            
            ax.set_title(title + '\n' + subtitle, fontsize=12)
            
            # Add info box
            props = dict(boxstyle='round', facecolor='white', alpha=0.8)
            ax.text(0.02, 0.03, info_text, transform=ax.transAxes, 
                    fontsize=10, verticalalignment='bottom', 
                    bbox=props)
            
            ax.set_xlabel('Time (seconds)')
            ax.set_ylabel('Ammo Remaining')
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend(loc='upper right', framealpha=0.9)
            ax.set_ylim(bottom=0)
            
            # Use only light theme style for plots
            plt.style.use('default')
            ax.spines['bottom'].set_color('#333333')
            ax.spines['top'].set_color('#333333') 
            ax.spines['right'].set_color('#333333')
            ax.spines['left'].set_color('#333333')
            ax.tick_params(axis='x', colors='#333333')
            ax.tick_params(axis='y', colors='#333333')
            ax.yaxis.label.set_color('#333333')
            ax.xaxis.label.set_color('#333333')
            ax.title.set_color('#333333')
            fig.patch.set_facecolor('#f5f5f5')
            ax.set_facecolor('#ffffff')
            
            st.pyplot(fig)
            
            # Removed detailed results table here
                    
    with tab3:
        st.header("Animated Ammo Consumption")
        st.markdown("Watch a real-time time-based simulation of ammo consumption!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            anim_total_ammo = st.number_input("Base Ammo", min_value=1, value=300, step=1, key="anim_ammo")
            anim_fire_rate = st.number_input("Fire Rate (shots/sec)", min_value=0.1, value=60.0, step=0.1, key="anim_fire")
            anim_reload_time = st.number_input("Reload Time (sec)", min_value=0.1, value=2.3, step=0.1, key="anim_reload")
            anim_ammo_bonus = st.number_input("Max Ammo Bonus (%)", min_value=0, value=0, step=1, key="anim_bonus")
        
        with col2:
            st.markdown("###### Weapon Type")
            anim_is_mg = st.checkbox("Machine Gun (MG)", key="anim_mg")
            st.markdown("##### Equipment")
            anim_equipment = st.radio(
                "",
                ["None", "Bastion Cube", "Resilience"],
                key="anim_equip"
            )
            anim_speed = st.slider("Animation Speed", min_value=0.5, max_value=5.0, value=1.0, step=0.5,
                                 help="Higher values make the simulation run faster")
        
        st.markdown("---")
        
        st.warning("Note: Click the Stop Animation button to pause the simulation and keep the last frame visible.")
        st.info("The simulation is time-based, showing exact per-second consumption.")
        
        # Create a better layout for the buttons
        col1, col2 = st.columns([3, 1])  # Use a wider column for text/info
        
        with col1:
            button_cols = st.columns(2)  # Create two equal columns for buttons
            
            with button_cols[0]:
                start_button = st.button("▶️ Start Animation", key="start_anim")
                
            with button_cols[1]:
                # Add the stop button with red styling
                stop_button = st.button("⏹️ Stop", key="stop_anim_button", 
                                   on_click=lambda: setattr(st.session_state, 'stop_animation', True))
                
        # Add CSS targeting specifically the stop button
        st.markdown("""
            <style>
            /* Target the stop button specifically */
            [data-testid="stButton"] button:contains("⏹️ Stop") {
                background-color: #e74c3c;
                color: white;
            }
            [data-testid="stButton"] button:contains("⏹️ Stop"):hover {
                background-color: #c0392b;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Set values based on equipment selection 
        anim_bastion_cube = anim_equipment == "Bastion Cube"
        anim_resilience = 29.69 if anim_equipment == "Resilience" else 0
            
        if start_button:
            # Reset stop flag before starting animation
            st.session_state.stop_animation = False
            create_animation(
                anim_total_ammo, 
                anim_fire_rate, 
                anim_reload_time, 
                anim_is_mg, 
                anim_bastion_cube, 
                anim_resilience, 
                anim_ammo_bonus,
                anim_speed
            )
    
    # Add footer
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This calculator helps NIKKE players optimize their weapon loadout by calculating uptime percentages and visualizing ammo consumption.
    
    The calculator takes into account:
    - Base weapon stats (ammo, fire rate, reload time)
    - Equipment (Bastion Cube or Resilience)
    - Machine Gun wind-up mechanics
    - Cover downtime during reloads
    - Ammo bonuses from skills or talents
                
    Author: David
    """)

if __name__ == "__main__":
    main()
