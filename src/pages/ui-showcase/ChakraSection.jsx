import { ChakraProvider, Button, Card, Badge } from '@chakra-ui/react';

export default function ChakraSection() {
  return (
    <ChakraProvider>
      <Card.Root maxW="sm">
        <Card.Header>
          <Card.Title>Chakra UI</Card.Title>
          <Card.Description>Accessible, composable component primitives.</Card.Description>
        </Card.Header>
        <Card.Body>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
            <Button colorPalette="teal">Primary</Button>
            <Button variant="outline">Outline</Button>
            <Button colorPalette="purple" variant="solid">
              Accent
            </Button>
          </div>
          <Badge colorPalette="teal">Active</Badge>
        </Card.Body>
      </Card.Root>
    </ChakraProvider>
  );
}
