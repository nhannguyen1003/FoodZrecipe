import { Icons } from "@/components/icons";
import { SidebarLink } from "@/components/side-bar-items";

type AdditionalLinks = {
  title: string;
  links: SidebarLink[];
};

export const defaultLinks: (productId: number) => SidebarLink[] = (
  productId: number
) => [
  {
    href: `/products/${productId}/subscribers`,
    title: "Subscribers",
    icon: Icons.users,
  },
  { href: `/products/${productId}/plans`, title: "Plans", icon: Icons.users },
  {
    href: "/roles-permissions",
    title: "Roles and Permission",
    icon: Icons.users,
  },
];

export const additionalLinks: AdditionalLinks[] = [];
