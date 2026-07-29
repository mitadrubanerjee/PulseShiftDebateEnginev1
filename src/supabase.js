import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = "https://qninwvhgbdzezflgkszb.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_Dvt-fSw-BSU4sso8nR_IEA_0FZXx3Ah";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export async function loadTrades() {
  return supabase.from("trades").select("*")
    .order("trade_date", { ascending: false })
    .order("created_at", { ascending: false });
}

export async function insertTrade(trade) {
  return supabase.from("trades").insert([trade]).select().single();
}

export async function deleteTrade(id) {
  return supabase.from("trades").delete().eq("id", id);
}