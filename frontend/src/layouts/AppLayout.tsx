import { Outlet, useLocation, Link } from 'react-router-dom'
import { Refrigerator, ShoppingCart, ChefHat, Droplets, BookOpen, Search } from 'lucide-react'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from '@/components/ui/sidebar'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import type { LucideIcon } from 'lucide-react'

const NAV_ITEMS: { path: string; label: string; icon: LucideIcon }[] = [
  { path: '/', label: '冷蔵庫', icon: Refrigerator },
  { path: '/shopping', label: '買い物', icon: ShoppingCart },
  { path: '/menu-suggest', label: '献立', icon: ChefHat },
  { path: '/recipes', label: 'レシピ', icon: Search },
  { path: '/condiments', label: '調味料', icon: Droplets },
  { path: '/ingredients', label: '食材', icon: BookOpen },
]

function BottomNav() {
  const location = useLocation()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background md:hidden">
      <div className="flex h-14 items-center justify-around">
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'flex flex-1 flex-col items-center gap-0.5 py-1 text-[10px]',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground',
              )}
            >
              <item.icon className="size-5" />
              <span>{item.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

export function AppLayout() {
  const location = useLocation()

  return (
    <>
      {/* Desktop: sidebar layout */}
      <div className="hidden md:contents">
        <SidebarProvider>
          <Sidebar>
            <SidebarHeader className="p-6">
              <img src="/logo.svg" alt="CookLoop" className="h-8" />
            </SidebarHeader>
            <SidebarContent>
              <SidebarGroup>
                <SidebarGroupLabel>メニュー</SidebarGroupLabel>
                <SidebarGroupContent>
                  <SidebarMenu>
                    {NAV_ITEMS.map((item) => (
                      <SidebarMenuItem key={item.path}>
                        <SidebarMenuButton
                          asChild
                          isActive={location.pathname === item.path}
                        >
                          <Link to={item.path}>
                            <item.icon className="size-4" />
                            <span>{item.label}</span>
                          </Link>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                  </SidebarMenu>
                </SidebarGroupContent>
              </SidebarGroup>
            </SidebarContent>
          </Sidebar>
          <SidebarInset>
            <header className="flex h-12 shrink-0 items-center gap-2 px-4 border-b">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mr-2 h-4" />
              <span className="text-sm font-medium text-muted-foreground">
                {NAV_ITEMS.find((item) => item.path === location.pathname)?.label}
              </span>
            </header>
            <main className="flex-1 p-4 overflow-auto">
              <Outlet />
            </main>
          </SidebarInset>
        </SidebarProvider>
      </div>

      {/* Mobile: bottom nav layout */}
      <div className="flex min-h-svh flex-col md:hidden">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4">
          <img src="/logo.svg" alt="CookLoop" className="h-6" />
          <Separator orientation="vertical" className="mx-2 h-4" />
          <span className="text-sm font-medium text-muted-foreground">
            {NAV_ITEMS.find((item) => item.path === location.pathname)?.label}
          </span>
        </header>
        <main className="flex-1 overflow-auto pb-16">
          <Outlet />
        </main>
        <BottomNav />
      </div>
    </>
  )
}
