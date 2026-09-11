// Icon Registry - Export Lucide React icons by category
import {
  Home,
  Search,
  Bell,
  Settings,
  User,
  LogOut,
  Menu,
  X as XIcon,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Plus,
  Minus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Download,
  Upload,
  Check,
  XCircle,
  AlertCircle,
  Info,
  Loader,
  Sun,
  Moon,
  Heart,
  Star,
  Share,
  Bookmark,
  Filter,
  Sort,
  RefreshCw,
  Mail,
  Phone,
  MapPin,
  Globe,
  Calendar,
  Clock,
  CreditCard,
  ShoppingCart,
  Package,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Database,
  Server,
  Cpu,
  Zap,
  Shield,
  Lock,
  Unlock,
  Key,
  MessageSquare,
  Send,
  Folder,
  File,
  FileText,
  Image,
  Video,
  Music,
  Bot,
  Brain,
  Sparkles,
  Wand2,
  Briefcase,
  Building,
  Users,
  UserPlus,
  LayoutDashboard,
  Grid,
  List,
  Table,
  Monitor,
  Smartphone,
  Tablet,
  Laptop,
} from 'lucide-react';

// Common Icons
export const CommonIcons = {
  Search,
  Bell,
  Settings,
  User,
  LogOut,
  Menu,
  X: XIcon,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Plus,
  Minus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  Download,
  Upload,
  Check,
  XCircle,
  AlertCircle,
  Info,
  Loader,
};

// UI Icons
export const UiIcons = { Sun, Moon, Heart, Star, Share, Bookmark, Filter, Sort, RefreshCw };

// Navigation Icons
export const NavigationIcons = { Home, Mail, Phone, MapPin, Globe, Calendar, Clock };

// E-commerce Icons
export const EcommerceIcons = {
  CreditCard,
  ShoppingCart,
  Package,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
};

// Dashboard Icons
export const DashboardIcons = {
  BarChart3,
  PieChart,
  Database,
  Server,
  TrendingUp,
  TrendingDown,
  LayoutDashboard,
  Grid,
  List,
  Table,
};

// AI Icons
export const AiIcons = { Cpu, Zap, Bot, Brain, Sparkles, Wand2 };

// Business Icons
export const BusinessIcons = { Briefcase, Building, Users, UserPlus };

// Auth Icons
export const AuthIcons = { Shield, Lock, Unlock, Key };

// Media Icons
export const MediaIcons = { Image, Video, Music, Folder, File, FileText };

// Device Icons
export const DeviceIcons = { Monitor, Smartphone, Tablet, Laptop };

// Helper to get icon by name
export function getIconByName(name) {
  const all = {
    ...CommonIcons,
    ...UiIcons,
    ...NavigationIcons,
    ...EcommerceIcons,
    ...DashboardIcons,
    ...AiIcons,
    ...BusinessIcons,
    ...AuthIcons,
    ...MediaIcons,
    ...DeviceIcons,
  };
  return all[name] || null;
}
