import { useState } from "react";
import Landing from "./components/Landing";
import HostView from "./components/HostView";
import TeamView from "./components/TeamView";

const ROLE_KEY = "enriquiz_role";

export default function App() {
  const [role, setRole] = useState(() => sessionStorage.getItem(ROLE_KEY));

  function selectRole(next) {
    sessionStorage.setItem(ROLE_KEY, next);
    setRole(next);
  }

  function clearRole() {
    sessionStorage.removeItem(ROLE_KEY);
    setRole(null);
  }

  if (role === "host") {
    return <HostView onBack={clearRole} />;
  }

  if (role === "team") {
    return <TeamView onBack={clearRole} />;
  }

  return <Landing onSelectRole={selectRole} />;
}
