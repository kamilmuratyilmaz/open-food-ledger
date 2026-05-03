export type UUID = string;
export type ISODate = string;       // "YYYY-MM-DD"
export type ISODateTime = string;
export type MealType = "breakfast" | "lunch" | "dinner" | "snack";

export interface AuthResponse {
  user_id: UUID;
  email: string;
  api_token: string;
}

export interface User {
  user_id: UUID;
  email: string;
  api_token: string;
  created_at: ISODateTime;
}

export interface EntryIn {
  food_name: string;
  weight_g: number;
  meal_type: MealType;
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sugar_g?: number;
  sodium_mg?: number;
  notes?: string | null;
  entry_date?: ISODate;
  entry_time?: string | null;
}

export type EntryUpdate = Partial<EntryIn>;

export interface Entry {
  id: UUID;
  entry_date: ISODate;
  entry_time: string | null;
  meal_type: MealType;
  food_name: string;
  weight_g: number;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
  sugar_g: number;
  sodium_mg: number;
  notes: string | null;
  created_at: ISODateTime;
}
