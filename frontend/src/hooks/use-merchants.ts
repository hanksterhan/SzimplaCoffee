import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export function useMerchants() {
  return useQuery({
    queryKey: ["merchants"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/merchants");
      if (error) throw error;
      return data;
    },
  });
}
