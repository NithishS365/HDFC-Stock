"""
Supabase Configuration and Client Setup
Provides singleton client instances for both service role and anon access
"""
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseConfig:
    """Centralized Supabase configuration"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not all([self.url, self.anon_key, self.service_key]):
            raise ValueError("Missing Supabase credentials in environment variables")
    
    @property
    def service_client(self) -> Client:
        """Get Supabase client with service role (write access)"""
        return create_client(self.url, self.service_key)
    
    @property
    def anon_client(self) -> Client:
        """Get Supabase client with anon key (read-only, for testing)"""
        return create_client(self.url, self.anon_key)


# Singleton instances
_config: Optional[SupabaseConfig] = None

def get_supabase_config() -> SupabaseConfig:
    """Get or create Supabase config singleton"""
    global _config
    if _config is None:
        _config = SupabaseConfig()
    return _config

def get_supabase_client(service_role: bool = True) -> Client:
    """
    Get Supabase client
    
    Args:
        service_role: If True, returns service role client (write access)
                     If False, returns anon client (read-only)
    """
    config = get_supabase_config()
    return config.service_client if service_role else config.anon_client
