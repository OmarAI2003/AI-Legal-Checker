#!/usr/bin/env python3
"""
Deploy all agents for Egyptian Legal Contract Analysis System
"""

import subprocess
import sys
import time

def deploy_all_agents():
    """Deploy all agents for the Egyptian Legal Contract Analysis System"""
    
    agents = [
        ("Contract Explanation Agent", "agents/contract_explanation_agent.py"),
        ("Contract Assessment Agent", "agents/contract_assessment_agent.py")
    ]
    
    results = {}
    
    for agent_name, script_path in agents:
        print(f"\n{'='*60}")
        print(f"Deploying {agent_name}...")
        print(f"{'='*60}")
        
        try:
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, check=True)
            
            print(f"✅ {agent_name} deployed successfully!")
            print(result.stdout)
            results[agent_name] = "SUCCESS"
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to deploy {agent_name}")
            print(f"Error: {e.stderr}")
            results[agent_name] = f"FAILED: {e.stderr}"
        
        # Wait between deployments
        if agent_name != agents[-1][0]:  # Don't wait after the last agent
            print("Waiting 60 seconds before next deployment...")
            time.sleep(60)
    
    print(f"\n{'='*60}")
    print("DEPLOYMENT SUMMARY")
    print(f"{'='*60}")
    
    for agent_name, status in results.items():
        print(f"{agent_name}: {status}")
    
    return results

if __name__ == "__main__":
    deploy_all_agents()