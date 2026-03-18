import * as React from "react";
import * as SelectPrimitive from "@radix-ui/react-select";
import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

type SelectProps = React.ComponentPropsWithoutRef<typeof SelectPrimitive.Root> & {
  debugName?: string;
};

// ── Debug context (name only) ──────────────────────────────────────────────────
const SelectDebugContext = React.createContext<string | null>(null);

// ── Selection shim context ─────────────────────────────────────────────────────
// Carries the callbacks needed to drive value+open changes from SelectItem.onClick
// when Radix's own pointerup-based selection is swallowed by React 19.
type SelectShimCtx = {
  onValueChange: ((v: string) => void) | undefined;
  setOpen: (open: boolean) => void;
};
const SelectShimContext = React.createContext<SelectShimCtx>({
  onValueChange: undefined,
  setOpen: () => {},
});

function logSelect(debugName: string | null, message: string, payload?: Record<string, unknown>) {
  if (!debugName) return;
  if (payload) {
    console.log(`[Select:${debugName}] ${message}`, payload);
    return;
  }
  console.log(`[Select:${debugName}] ${message}`);
}

function Select({
  children,
  debugName,
  onOpenChange,
  onValueChange,
  open,
  value,
  ...props
}: SelectProps) {
  const [observedOpen, setObservedOpen] = React.useState(false);
  const resolvedOpen = open ?? observedOpen;

  const setOpen = React.useCallback(
    (nextOpen: boolean) => {
      setObservedOpen(nextOpen);
      onOpenChange?.(nextOpen);
    },
    [onOpenChange]
  );

  const handleOpenChange = React.useCallback(
    (nextOpen: boolean) => {
      logSelect(debugName ?? null, "onOpenChange", {
        previousOpen: resolvedOpen,
        nextOpen,
        value,
      });
      setOpen(nextOpen);
    },
    [debugName, resolvedOpen, value, setOpen]
  );

  React.useEffect(() => {
    logSelect(debugName ?? null, "props changed", { open: resolvedOpen, value });
  }, [debugName, resolvedOpen, value]);

  const shimCtx = React.useMemo<SelectShimCtx>(
    () => ({
      onValueChange,
      setOpen,
    }),
    [onValueChange, setOpen]
  );

  return (
    <SelectDebugContext.Provider value={debugName ?? null}>
      <SelectShimContext.Provider value={shimCtx}>
        <SelectPrimitive.Root
          {...props}
          {...(open !== undefined ? { open } : {})}
          value={value}
          onOpenChange={handleOpenChange}
          onValueChange={(nextValue) => {
            logSelect(debugName ?? null, "onValueChange (radix)", { previousValue: value, nextValue, open: resolvedOpen });
            onValueChange?.(nextValue);
          }}
        >
          {children}
        </SelectPrimitive.Root>
      </SelectShimContext.Provider>
    </SelectDebugContext.Provider>
  );
}

const SelectGroup = SelectPrimitive.Group;
const SelectValue = SelectPrimitive.Value;

const SelectTrigger = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger>
>(({ className, children, onClick, onPointerDown, ...props }, ref) => {
  const debugName = React.useContext(SelectDebugContext);
  const pointerTypeRef = React.useRef<string>("mouse");

  return (
    <SelectPrimitive.Trigger
      ref={ref}
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-md border border-input [background-color:hsl(var(--background))] px-3 py-2 text-sm ring-offset-background placeholder:[color:hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 [&>span]:line-clamp-1",
        className
      )}
      onPointerDown={(e) => {
        pointerTypeRef.current = e.pointerType;
        logSelect(debugName, "trigger pointerdown", {
          pointerType: e.pointerType,
          button: e.button,
          ctrlKey: e.ctrlKey,
        });
        onPointerDown?.(e);
      }}
      onClick={(e) => {
        logSelect(debugName, "trigger click", { pointerType: pointerTypeRef.current });
        onClick?.(e);
      }}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon asChild>
        <ChevronDown className="h-4 w-4 opacity-50" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  );
});
SelectTrigger.displayName = SelectPrimitive.Trigger.displayName;

const SelectScrollUpButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollUpButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollUpButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollUpButton
    ref={ref}
    className={cn("flex cursor-default items-center justify-center py-1", className)}
    {...props}
  >
    <ChevronUp className="h-4 w-4" />
  </SelectPrimitive.ScrollUpButton>
));
SelectScrollUpButton.displayName = SelectPrimitive.ScrollUpButton.displayName;

const SelectScrollDownButton = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.ScrollDownButton>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.ScrollDownButton>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.ScrollDownButton
    ref={ref}
    className={cn("flex cursor-default items-center justify-center py-1", className)}
    {...props}
  >
    <ChevronDown className="h-4 w-4" />
  </SelectPrimitive.ScrollDownButton>
));
SelectScrollDownButton.displayName = SelectPrimitive.ScrollDownButton.displayName;

const SelectContent = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>
>(({ className, children, position = "popper", onCloseAutoFocus, onEscapeKeyDown, onPointerDownOutside, ...props }, ref) => {
  const debugName = React.useContext(SelectDebugContext);

  React.useEffect(() => {
    logSelect(debugName, "content mounted");
    return () => logSelect(debugName, "content unmounted");
  }, [debugName]);

  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        ref={ref}
        className={cn(
          "relative z-50 max-h-96 min-w-[8rem] overflow-hidden rounded-md border shadow-md [background-color:hsl(var(--popover))] [color:hsl(var(--popover-foreground))] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
          position === "popper" &&
            "data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1 data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1",
          className
        )}
        position={position}
        onCloseAutoFocus={(event) => {
          logSelect(debugName, "content onCloseAutoFocus");
          onCloseAutoFocus?.(event);
        }}
        onEscapeKeyDown={(event) => {
          logSelect(debugName, "content onEscapeKeyDown");
          onEscapeKeyDown?.(event);
        }}
        onPointerDownOutside={(event) => {
          logSelect(debugName, "content onPointerDownOutside", {
            target: event.target instanceof HTMLElement ? event.target.tagName : "unknown",
          });
          onPointerDownOutside?.(event);
        }}
        {...props}
      >
        <SelectScrollUpButton />
        <SelectPrimitive.Viewport
          className={cn(
            "p-1",
            position === "popper" &&
              "h-[var(--radix-select-trigger-height)] w-full min-w-[var(--radix-select-trigger-width)]"
          )}
        >
          {children}
        </SelectPrimitive.Viewport>
        <SelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  );
});
SelectContent.displayName = SelectPrimitive.Content.displayName;

const SelectLabel = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Label
    ref={ref}
    className={cn("py-1.5 pl-8 pr-2 text-sm font-semibold", className)}
    {...props}
  />
));
SelectLabel.displayName = SelectPrimitive.Label.displayName;

const SelectItem = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>
>(({ className, children, onClick, ...props }, ref) => {
  const debugName = React.useContext(SelectDebugContext);
  // Shim: drive value+close directly on click for mouse events.
  // Radix drives selection via pointerup for mouse, but React 19 swallows
  // pointerup events on portal content — onClick is reliable on all inputs.
  const { onValueChange, setOpen } = React.useContext(SelectShimContext);

  return (
    <SelectPrimitive.Item
      ref={ref}
      className={cn(
        "relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
      onClick={(e) => {
        logSelect(debugName, "item click (shim)", {
          value: typeof props.value === "string" ? props.value : undefined,
        });
        // Fire our shim directly — Radix's pointerup path may be swallowed.
        if (!props.disabled && typeof props.value === "string") {
          onValueChange?.(props.value);
          setOpen(false);
        }
        onClick?.(e);
      }}
      onPointerUp={() => {
        logSelect(debugName, "item pointerup", {
          value: typeof props.value === "string" ? props.value : undefined,
        });
      }}
      {...props}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <Check className="h-4 w-4" />
        </SelectPrimitive.ItemIndicator>
      </span>
      <SelectPrimitive.ItemText>{children}</SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  );
});
SelectItem.displayName = SelectPrimitive.Item.displayName;

const SelectSeparator = React.forwardRef<
  React.ElementRef<typeof SelectPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <SelectPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px [background-color:hsl(var(--muted))]", className)}
    {...props}
  />
));
SelectSeparator.displayName = SelectPrimitive.Separator.displayName;

export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
};
