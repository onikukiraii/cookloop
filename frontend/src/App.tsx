import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { FridgePage } from '@/pages/FridgePage'
import { ShoppingPage } from '@/pages/ShoppingPage'
import { MenuSuggestPage } from '@/pages/MenuSuggestPage'
import { RecipePage } from '@/pages/RecipePage'
import { CondimentPage } from '@/pages/CondimentPage'
import { IngredientMasterPage } from '@/pages/IngredientMasterPage'
import { Toaster } from '@/components/ui/sonner'
import { SuggestJobMonitor } from '@/components/SuggestJobMonitor'

function App() {
  return (
    <BrowserRouter>
      <SuggestJobMonitor />
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<FridgePage />} />
          <Route path="/shopping" element={<ShoppingPage />} />
          <Route path="/menu-suggest" element={<MenuSuggestPage />} />
          <Route path="/recipes" element={<RecipePage />} />
          <Route path="/condiments" element={<CondimentPage />} />
          <Route path="/ingredients" element={<IngredientMasterPage />} />
        </Route>
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}

export default App
