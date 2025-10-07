import React from "react";
import { createBrowserRouter } from "react-router-dom";
import MapPageRouteDemo from "@/pages/MapPageRouteDemo";
export const router = createBrowserRouter([{ path: "/map/route-demo", element: <MapPageRouteDemo /> }]);
