import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/api/client";
import type { components } from "@/api/schema";

export type BrewFeedbackOut = components["schemas"]["BrewFeedbackOut"];
export type BrewFeedbackCreate = components["schemas"]["BrewFeedbackCreate"];
export type BrewFeedbackUpdate = components["schemas"]["BrewFeedbackUpdate"];

export function usePurchaseFeedback(purchaseId: number) {
  return useQuery({
    queryKey: ["feedback", purchaseId],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/api/v1/purchases/{purchase_id}/feedback",
        { params: { path: { purchase_id: purchaseId } } }
      );
      if (error) throw error;
      return data as BrewFeedbackOut[];
    },
    enabled: purchaseId > 0,
  });
}

export function useAddFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      purchaseId,
      body,
    }: {
      purchaseId: number;
      body: BrewFeedbackCreate;
    }) => {
      const { data, error } = await api.POST(
        "/api/v1/purchases/{purchase_id}/feedback",
        {
          params: { path: { purchase_id: purchaseId } },
          body,
        }
      );
      if (error) throw error;
      return data as BrewFeedbackOut;
    },
    onSuccess: (_data, { purchaseId }) => {
      qc.invalidateQueries({ queryKey: ["feedback", purchaseId] });
      qc.invalidateQueries({ queryKey: ["purchases"] });
      toast.success("Feedback saved");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}

export function useUpdateFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      body,
    }: {
      id: number;
      body: BrewFeedbackUpdate;
    }) => {
      const { data, error } = await api.PUT(
        "/api/v1/feedback/{feedback_id}",
        {
          params: { path: { feedback_id: id } },
          body,
        }
      );
      if (error) throw error;
      return data as BrewFeedbackOut;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["feedback"] });
      toast.success("Feedback updated");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}

export function useDeleteFeedback() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, purchaseId }: { id: number; purchaseId: number }) => {
      const { error } = await api.DELETE(
        "/api/v1/feedback/{feedback_id}",
        { params: { path: { feedback_id: id } } }
      );
      if (error) throw error;
      return purchaseId;
    },
    onSuccess: (_data, { purchaseId }) => {
      qc.invalidateQueries({ queryKey: ["feedback", purchaseId] });
      qc.invalidateQueries({ queryKey: ["purchases"] });
      toast.success("Deleted successfully");
    },
    onError: (err: Error) => {
      toast.error(`Something went wrong: ${err.message}`);
    },
  });
}
