import{q as a,N as n,u as l,s as o}from"./index.Ba-G_K02.js";import{C as i,I as p}from"./indian-rupee.Cuw-XzWc.js";import{C as y}from"./calendar-days.BFchCZ5V.js";import{U as d}from"./users.H0Iv4KT9.js";/**
 * @license lucide-vue-next v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const h=a("ChartColumnIcon",[["path",{d:"M3 3v16a2 2 0 0 0 2 2h16",key:"c24i48"}],["path",{d:"M18 17V9",key:"2bz60n"}],["path",{d:"M13 17V5",key:"1frdt8"}],["path",{d:"M8 17v-3",key:"17ska0"}]]);/**
 * @license lucide-vue-next v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const k=a("CircleUserIcon",[["circle",{cx:"12",cy:"12",r:"10",key:"1mglay"}],["circle",{cx:"12",cy:"10",r:"3",key:"ilqhr7"}],["path",{d:"M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662",key:"154egf"}]]);/**
 * @license lucide-vue-next v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const m=a("FingerprintIcon",[["path",{d:"M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4",key:"1nerag"}],["path",{d:"M14 13.12c0 2.38 0 6.38-1 8.88",key:"o46ks0"}],["path",{d:"M17.29 21.02c.12-.6.43-2.3.5-3.02",key:"ptglia"}],["path",{d:"M2 12a10 10 0 0 1 18-6",key:"ydlgp0"}],["path",{d:"M2 16h.01",key:"1gqxmh"}],["path",{d:"M21.8 16c.2-2 .131-5.354 0-6",key:"drycrb"}],["path",{d:"M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2",key:"1tidbn"}],["path",{d:"M8.65 22c.21-.66.45-1.32.57-2",key:"13wd9y"}],["path",{d:"M9 6.8a6 6 0 0 1 9 5.2v2",key:"1fr1j5"}]]);/**
 * @license lucide-vue-next v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const u=a("HouseIcon",[["path",{d:"M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8",key:"5wwlr5"}],["path",{d:"M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",key:"1d0kgt"}]]);/**
 * @license lucide-vue-next v0.468.0 - ISC
 *
 * This source code is licensed under the ISC license.
 * See the LICENSE file in the root directory of this source tree.
 */const M=a("UsersRoundIcon",[["path",{d:"M18 21a8 8 0 0 0-16 0",key:"3ypg7q"}],["circle",{cx:"10",cy:"8",r:"5",key:"o932ke"}],["path",{d:"M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3",key:"10s06x"}]]),f=[{to:"/",label:"Dashboard",icon:u,spot:"profile",access:"employee"},{to:"/check-in",label:"Check In/Out",icon:m,spot:"checkin",access:"employee"},{to:"/attendance",label:"Attendance",icon:i,spot:"attendance",access:"employee"},{to:"/salary",label:"Salary Slip",icon:p,spot:"salary",access:"employee"},{to:"/holidays",label:"Holiday List",icon:y,spot:"holiday",access:"employee"},{to:"/directory",label:"Directory",icon:M,spot:"directory",access:"team"},{to:"/team",label:"Team Attendance",icon:d,spot:"team",access:"team"},{to:"/exceptions",label:"Exceptions",icon:n,spot:"alert",access:"team"},{to:"/hr",label:"HR Dashboard",icon:h,spot:"chart",access:"hr"},{to:"/profile",label:"My Profile",icon:k,spot:"profile"}];function x(){const t=l();function c(e){return e.access==="employee"?t.isEmployee:e.access==="team"?t.hasTeamAccess:e.access==="hr"?t.isHr:!0}const s=o(()=>f.filter(c)),r=o(()=>s.value.filter(e=>["/check-in","/holidays","/attendance","/team","/exceptions","/hr"].includes(e.to)).slice(0,5));return{items:s,actions:r,allowed:c}}export{k as C,u as H,M as U,x as u};
