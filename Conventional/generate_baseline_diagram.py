import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_professional_diagram():
    # Use a style closer to technical papers
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
    
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.axis('off')
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    
    # Properties
    primary_color = '#2c3e50' # Dark Blue/Grey
    accent_color = '#3498db'  # Blue
    highlight_color = '#e74c3c' # Red/Orange for action? Or keep it neutral.
    box_props = dict(boxstyle='round,pad=0.8', facecolor='white', edgecolor=primary_color, linewidth=1.5)
    container_props = dict(boxstyle='round,pad=0.4', facecolor='#f8f9fa', edgecolor='#bdc3c7', linewidth=1, linestyle='--')
    
    # 1. Input Node (Left)
    ax.text(8, 20, "User Prompt\n(Input)", ha='center', va='center', size=9, weight='bold', color=primary_color,
            bbox=dict(boxstyle='circle,pad=0.5', fc='#ecf0f1', ec=primary_color))
            
    # Arrow 1->2
    ax.annotate("", xy=(18, 20), xytext=(12, 20), 
                arrowprops=dict(arrowstyle='-|>', color=primary_color, lw=2))
                
    # 2. Main Processing Unit (The Single Agent)
    # Draw a large container rectangle representing the "Single-Agent" boundary
    # x=18 to x=82, y=5 to y=35
    rect = patches.FancyBboxPatch((18, 5), 64, 30, boxstyle="round,pad=0.2", 
                                  linewidth=1.5, edgecolor=accent_color, facecolor='#f0f8ff')
    ax.add_patch(rect)
    
    ax.text(50, 32, "Single-Agent Orchestration Scope", ha='center', va='center', size=10, weight='bold', color=accent_color)
    
    # Phases inside the container
    phases = [
        ("Requirements\nAnalysis", 0.0),
        ("High-Level\nDesign", 1.0), 
        ("Code\nGeneration", 2.0),
        ("Static\nValidation", 3.0)
    ]
    
    start_x = 26
    step_x = 15
    y_pos = 18
    
    for i, (label, offset) in enumerate(phases):
        x = start_x + (i * step_x)
        
        # Phase Box
        ax.text(x, y_pos, label, ha='center', va='center', size=8, 
                bbox=dict(boxstyle='round,pad=0.5', fc='white', ec=primary_color, lw=1))
        
        # Arrow to next phase
        if i < len(phases) - 1:
            next_x = start_x + ((i+1) * step_x)
            ax.annotate("", xy=(next_x - 4, y_pos), xytext=(x + 4, y_pos), 
                        arrowprops=dict(arrowstyle='->', color=primary_color, lw=1.5))
                        
    # 3. Output Node (Right)
    # Arrow out
    ax.annotate("", xy=(90, 20), xytext=(82, 20), 
                arrowprops=dict(arrowstyle='-|>', color=primary_color, lw=2))
                
    # Output Box
    ax.text(94, 20, "Final\nApplication", ha='center', va='center', size=9, weight='bold', color=primary_color,
            bbox=dict(boxstyle='round,pad=0.6', fc='#e8f6f3', ec='#1abc9c', lw=1.5))

    plt.tight_layout()
    plt.savefig('baseline_system_v2.png', dpi=300, bbox_inches='tight')
    print("New diagram generated: baseline_system_v2.png")

if __name__ == "__main__":
    create_professional_diagram()
