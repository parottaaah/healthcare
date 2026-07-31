import apiClient from "./client";

export type BillStatus = "uploaded" | "parsed" | "reviewed";

export interface BillLineItem {
  id: string;
  description: string;
  amount: number;
  flagged_overcharge: boolean;
  explanation?: string | null;
}

export interface Bill {
  id: string;
  user_id: string;
  raw_file_url: string;
  total_amount: number;
  currency: string;
  status: BillStatus;
  created_at: string;
  updated_at: string;
  line_items?: BillLineItem[];
}

export async function uploadBill(file: File): Promise<Bill> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<Bill>("/bills/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getBills(): Promise<Bill[]> {
  const { data } = await apiClient.get<Bill[]>("/bills");
  return data;
}

export async function getBill(id: string): Promise<Bill> {
  const { data } = await apiClient.get<Bill>(`/bills/${id}`);
  return data;
}

export async function explainBill(id: string): Promise<Bill> {
  const { data } = await apiClient.post<Bill>(`/bills/${id}/explain`);
  return data;
}
