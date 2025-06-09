from supabase import Client, create_client

from prophet.config import SupaConfig

c = SupaConfig.from_env()
supabase: Client = create_client(c.URL, c.KEY)


if __name__ == "__main__":
    print(supabase)
