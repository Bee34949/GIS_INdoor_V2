import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import MapPageRouteDemo from "@/pages/MapPageRouteDemo";
import VectorTilesDemo from "@/pages/VectorTilesDemo";

function NotFound() {
  return (
    <div style={{padding:24}}>
      <h1>404</h1>
      <ul>
        <li><a href="/map/route-demo">/map/route-demo</a></li>
        <li><a href="/map/tiles-demo">/map/tiles-demo</a></li>
      </ul>
    </div>
  );
}

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/map/route-demo" replace /> }, // redirect root
  { path: "/map/route-demo", element: <MapPageRouteDemo /> },        // หน้าเดิม (SVG)
  { path: "/map/tiles-demo", element: <VectorTilesDemo /> },         // หน้า Vector Tiles
  { path: "*", element: <NotFound /> }
]);