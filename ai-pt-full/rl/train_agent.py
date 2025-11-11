import os
import sys
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback

# Add project root to path to import the environment
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rl.rl_env_web import WebAppPenTestEnv

# --- Configuration ---
# IMPORTANT: This should be a safe, authorized target. Running a local instance
# of a vulnerable app like OWASP Juice Shop or DVWA is highly recommended.
TARGET_URL = os.environ.get("RL_TARGET_URL", "http://localhost:3000") # Default to local Juice Shop

LOG_DIR = "rl/logs/"
MODEL_SAVE_PATH = "rl/ppo_web_pentest_agent"
TOTAL_TIMESTEPS = 20000

def train_rl_agent():
    """
    Trains a PPO agent on the custom web penetration testing environment.
    """
    print(f"[*] Starting RL training for target: {TARGET_URL}")
    print("[!] Ensure the target is running and accessible.")

    # --- 1. Create and Vectorize the Environment ---
    # We use DummyVecEnv to wrap our custom environment, which is standard for SB3.
    env = DummyVecEnv([lambda: WebAppPenTestEnv(target_url=TARGET_URL)])

    # --- 2. Create the PPO Model ---
    # We use the 'MlpPolicy' because our observation space is a flat vector.
    # The policy network will be a Multi-Layer Perceptron.
    model = PPO(
        'MlpPolicy',
        env,
        verbose=1,
        tensorboard_log=LOG_DIR,
        learning_rate=0.0003,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.0,
        vf_coef=0.5,
        max_grad_norm=0.5
    )

    # --- 3. Set up Callbacks ---
    # Save a checkpoint of the model every 1000 steps
    checkpoint_callback = CheckpointCallback(save_freq=1000, save_path=LOG_DIR, name_prefix='rl_model')

    # --- 4. Train the Model ---
    print("[*] Starting model training...")
    try:
        model.learn(
            total_timesteps=TOTAL_TIMESTEPS,
            callback=checkpoint_callback
        )
    except Exception as e:
        print(f"\n[!] An error occurred during training: {e}")
        print("[!] This might be due to the target application not being reachable or crashing.")
        print("[!] Please check the target and try again.")
        return

    # --- 5. Save the Final Model ---
    print(f"[*] Training complete. Saving final model to {MODEL_SAVE_PATH}")
    model.save(MODEL_SAVE_PATh)

    print("\n--- RL Agent Training Finished ---")
    print(f"To see training progress, run: tensorboard --logdir {LOG_DIR}")


if __name__ == '__main__':
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    train_rl_agent()
